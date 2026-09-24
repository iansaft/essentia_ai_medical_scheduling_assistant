import random
from collections.abc import Callable
from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog
from pydantic import TypeAdapter
from redis import Redis
from redis.exceptions import RedisError

from essentia_api.core.config import Settings
from essentia_api.schemas.availability import AvailableSlotResponse

AVAILABILITY_CACHE_NAMESPACE = "availability"
AVAILABILITY_CACHE_VERSION = "v1"
ALL_FILTER = "all"

JitterFn = Callable[[], int]

_list_adapter: TypeAdapter[list[AvailableSlotResponse]] = TypeAdapter(
    list[AvailableSlotResponse],
)

logger = structlog.get_logger(
    "essentia_api.cache.availability",
)

__all__ = [
    "ALL_FILTER",
    "AVAILABILITY_CACHE_NAMESPACE",
    "AVAILABILITY_CACHE_VERSION",
    "AvailabilityCache",
    "build_availability_cache_key",
    "build_availability_invalidation_keys",
    "create_availability_cache",
    "deserialize_availability_slots",
    "serialize_availability_slots",
]


def _cache_key(
    *,
    service_part: str,
    doctor_part: str,
    date_part: str,
) -> str:
    return (
        f"{AVAILABILITY_CACHE_NAMESPACE}"
        f":{AVAILABILITY_CACHE_VERSION}"
        f":{service_part}:{doctor_part}:{date_part}"
    )


def build_availability_cache_key(
    *,
    service_id: UUID | None,
    doctor_id: UUID | None,
    target_date: date | None,
) -> str:
    """
    Build the deterministic cache key for one availability query.

    Absent optional filters are represented by the literal ``all`` so that
    distinct queries can never collide and every key stays human-readable.
    """
    return _cache_key(
        service_part=(
            str(service_id)
            if service_id is not None
            else ALL_FILTER
        ),
        doctor_part=(
            str(doctor_id)
            if doctor_id is not None
            else ALL_FILTER
        ),
        date_part=(
            target_date.isoformat()
            if target_date is not None
            else ALL_FILTER
        ),
    )


def build_availability_invalidation_keys(
    *,
    service_id: UUID,
    doctor_id: UUID,
    business_date: date,
) -> list[str]:
    """
    Return every cache key that may contain the given slot.

    A query includes the slot when each of its filters is either absent
    (``all``) or matches the slot, which yields the full cross product of
    ``{service_id, all} x {doctor_id, all} x {date, all}``.
    """
    service_part = str(service_id)
    doctor_part = str(doctor_id)
    date_part = business_date.isoformat()

    return [
        _cache_key(
            service_part=service_filter,
            doctor_part=doctor_filter,
            date_part=date_filter,
        )
        for service_filter in (service_part, ALL_FILTER)
        for doctor_filter in (doctor_part, ALL_FILTER)
        for date_filter in (date_part, ALL_FILTER)
    ]


def serialize_availability_slots(
    slots: list[AvailableSlotResponse],
) -> bytes:
    """Serialize slots to stable JSON bytes (never pickle)."""
    return _list_adapter.dump_json(slots)


def deserialize_availability_slots(
    payload: str | bytes,
) -> list[AvailableSlotResponse]:
    """Deserialize a cached JSON payload back into response models."""
    return _list_adapter.validate_json(payload)


def _filter_log_fields(
    *,
    service_id: UUID | None,
    doctor_id: UUID | None,
    target_date: date | None,
) -> dict[str, str | None]:
    return {
        "service_id": (
            str(service_id)
            if service_id is not None
            else None
        ),
        "doctor_id": (
            str(doctor_id)
            if doctor_id is not None
            else None
        ),
        "date": (
            target_date.isoformat()
            if target_date is not None
            else None
        ),
    }


class AvailabilityCache:
    """
    Cache-Aside access to cached availability reads.

    Redis is an optimization only: every method fails open. Read, write,
    and invalidation problems are logged and swallowed so PostgreSQL
    remains the sole source of truth and Redis outages never surface as
    HTTP errors or undo completed mutations.
    """

    def __init__(
        self,
        *,
        client: Redis | None,
        settings: Settings,
        jitter_fn: JitterFn | None = None,
    ) -> None:
        self._client = client
        self._settings = settings
        self._jitter_fn = jitter_fn

    @property
    def client(self) -> Redis | None:
        return self._client

    @property
    def enabled(self) -> bool:
        return (
            self._client is not None
            and self._settings.availability_cache_enabled
        )

    def _default_jitter(self) -> int:
        max_jitter = (
            self._settings.availability_cache_ttl_jitter_seconds
        )
        if max_jitter <= 0:
            return 0
        return random.randint(0, max_jitter)

    def effective_ttl_seconds(self) -> int:
        """Base TTL plus a bounded positive jitter, in seconds."""
        jitter = (
            self._jitter_fn()
            if self._jitter_fn is not None
            else self._default_jitter()
        )
        return (
            self._settings.availability_cache_ttl_seconds
            + jitter
        )

    def get(
        self,
        *,
        service_id: UUID | None,
        doctor_id: UUID | None,
        target_date: date | None,
    ) -> list[AvailableSlotResponse] | None:
        """
        Return the cached slots for the query, or ``None`` on a miss.

        ``None`` means "consult PostgreSQL". A cached empty list is a hit
        and comes back as ``[]``. Redis failures are logged and treated
        as a miss (fail-open).
        """
        client = self._client
        if client is None or not self._settings.availability_cache_enabled:
            return None

        cache_key = build_availability_cache_key(
            service_id=service_id,
            doctor_id=doctor_id,
            target_date=target_date,
        )
        log_fields = _filter_log_fields(
            service_id=service_id,
            doctor_id=doctor_id,
            target_date=target_date,
        )

        try:
            payload = client.get(cache_key)
        except (RedisError, OSError) as exc:
            logger.error(
                "availability_cache_read_error",
                cache_key=cache_key,
                error=str(exc),
                **log_fields,
            )
            return None

        if payload is None:
            logger.info(
                "availability_cache_miss",
                cache_key=cache_key,
                **log_fields,
            )
            return None

        try:
            slots = deserialize_availability_slots(payload)
        except ValueError as exc:
            logger.error(
                "availability_cache_read_error",
                cache_key=cache_key,
                error=str(exc),
                reason="invalid_cached_payload",
            )
            return None

        logger.info(
            "availability_cache_hit",
            cache_key=cache_key,
            **log_fields,
        )
        return slots

    def set(
        self,
        *,
        service_id: UUID | None,
        doctor_id: UUID | None,
        target_date: date | None,
        slots: list[AvailableSlotResponse],
    ) -> None:
        """
        Store the query result in Redis with a short TTL.

        Empty lists are cached like any other result. Failures are
        logged and swallowed so the PostgreSQL result is still returned.
        """
        client = self._client
        if client is None or not self._settings.availability_cache_enabled:
            return

        cache_key = build_availability_cache_key(
            service_id=service_id,
            doctor_id=doctor_id,
            target_date=target_date,
        )
        log_fields = _filter_log_fields(
            service_id=service_id,
            doctor_id=doctor_id,
            target_date=target_date,
        )
        ttl_seconds = self.effective_ttl_seconds()

        try:
            payload = serialize_availability_slots(slots)
            client.set(
                cache_key,
                payload,
                ex=ttl_seconds,
            )
        except (RedisError, OSError, ValueError) as exc:
            logger.error(
                "availability_cache_write_error",
                cache_key=cache_key,
                error=str(exc),
                **log_fields,
            )
            return

        logger.info(
            "availability_cache_set",
            cache_key=cache_key,
            ttl_seconds=ttl_seconds,
            **log_fields,
        )

    def invalidate_for_appointment(
        self,
        *,
        service_id: UUID,
        doctor_id: UUID,
        starts_at: datetime,
    ) -> None:
        """
        Remove every availability key that may contain the booked slot.

        Only call after the PostgreSQL transaction committed. Never
        raises: a failed invalidation leaves stale data to expire via
        TTL instead of endangering a completed mutation.
        """
        client = self._client
        if client is None or not self._settings.availability_cache_enabled:
            return

        try:
            business_date = self._business_date(starts_at)
            cache_keys = build_availability_invalidation_keys(
                service_id=service_id,
                doctor_id=doctor_id,
                business_date=business_date,
            )
            removed = client.delete(*cache_keys)
        except Exception as exc:  # noqa: BLE001 -- invalidation must never fail a committed mutation
            # Log the problem and let TTL bound staleness instead.
            logger.error(
                "availability_cache_invalidation_error",
                error=str(exc),
                service_id=str(service_id),
                doctor_id=str(doctor_id),
                starts_at=starts_at.isoformat(),
            )
            return

        logger.info(
            "availability_cache_invalidation",
            cache_keys=cache_keys,
            removed=removed,
            service_id=str(service_id),
            doctor_id=str(doctor_id),
            date=business_date.isoformat(),
        )

    def _business_date(
        self,
        starts_at: datetime,
    ) -> date:
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=UTC)

        return starts_at.astimezone(
            ZoneInfo(
                self._settings.business_timezone,
            ),
        ).date()


def create_availability_cache(
    settings: Settings,
    client: Redis | None,
) -> AvailabilityCache:
    """Build the cache wrapper owned by one application instance."""
    return AvailabilityCache(
        client=client,
        settings=settings,
    )
