from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from essentia_api.cache.availability import (
    ALL_FILTER,
    AVAILABILITY_CACHE_NAMESPACE,
    AVAILABILITY_CACHE_VERSION,
    AvailabilityCache,
    _filter_log_fields,
    build_availability_cache_key,
    build_availability_invalidation_keys,
    deserialize_availability_slots,
    serialize_availability_slots,
)
from essentia_api.cache.redis import create_redis_client
from essentia_api.core.config import Settings
from essentia_api.schemas.availability import AvailableSlotResponse

SERVICE_A = uuid4()
SERVICE_B = uuid4()
DOCTOR_A = uuid4()
DOCTOR_B = uuid4()
DAY_1 = date(2027, 4, 12)
DAY_2 = date(2027, 4, 13)


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "db_user": "test",
        "db_password": "test",
        "redis_host": "127.0.0.1",
        "redis_port": 6379,
        "redis_password": None,
        "redis_db": 0,
        "redis_socket_timeout": 2.0,
        "redis_connect_timeout": 2.0,
        "availability_cache_enabled": True,
        "availability_cache_ttl_seconds": 30,
        "availability_cache_ttl_jitter_seconds": 10,
        "business_timezone": "America/Sao_Paulo",
    }
    base.update(overrides)
    return Settings(**base)


def _slot(**overrides: Any) -> AvailableSlotResponse:
    base: dict[str, Any] = {
        "id": uuid4(),
        "doctor_id": DOCTOR_A,
        "doctor_name": "Dr. Helena Costa",
        "service_id": SERVICE_A,
        "service_code": "CARDIO-INIT",
        "service_name": "Cardiology Initial Consultation",
        "price": Decimal("320.00"),
        "currency": "BRL",
        "starts_at": datetime(
            2027,
            4,
            12,
            13,
            0,
            tzinfo=UTC,
        ),
        "ends_at": datetime(
            2027,
            4,
            12,
            13,
            45,
            tzinfo=UTC,
        ),
    }
    base.update(overrides)
    return AvailableSlotResponse(**base)


def _cache(
    *,
    settings: Settings | None = None,
    client: Redis | MagicMock | None = None,
    jitter_fn=None,
) -> AvailabilityCache:
    return AvailabilityCache(
        client=client,  # type: ignore[arg-type]
        settings=settings or _settings(),
        jitter_fn=jitter_fn,
    )


def test_build_key_uses_namespaced_versioned_format() -> None:
    key = build_availability_cache_key(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
    )

    assert key == (
        f"{AVAILABILITY_CACHE_NAMESPACE}:"
        f"{AVAILABILITY_CACHE_VERSION}:"
        f"{SERVICE_A}:{DOCTOR_A}:{DAY_1.isoformat()}"
    )


def test_build_key_represents_absent_filters_as_all() -> None:
    key = build_availability_cache_key(
        service_id=None,
        doctor_id=None,
        target_date=None,
    )

    assert key == (
        f"{AVAILABILITY_CACHE_NAMESPACE}:"
        f"{AVAILABILITY_CACHE_VERSION}:"
        f"{ALL_FILTER}:{ALL_FILTER}:{ALL_FILTER}"
    )


def test_build_key_is_deterministic() -> None:
    first = build_availability_cache_key(
        service_id=SERVICE_A,
        doctor_id=None,
        target_date=DAY_1,
    )
    second = build_availability_cache_key(
        service_id=SERVICE_A,
        doctor_id=None,
        target_date=DAY_1,
    )

    assert first == second


def test_build_key_separates_distinct_queries() -> None:
    keys = {
        build_availability_cache_key(
            service_id=SERVICE_A,
            doctor_id=DOCTOR_A,
            target_date=DAY_1,
        ),
        build_availability_cache_key(
            service_id=SERVICE_A,
            doctor_id=DOCTOR_B,
            target_date=DAY_1,
        ),
        build_availability_cache_key(
            service_id=SERVICE_A,
            doctor_id=DOCTOR_A,
            target_date=DAY_2,
        ),
        build_availability_cache_key(
            service_id=SERVICE_B,
            doctor_id=DOCTOR_A,
            target_date=DAY_1,
        ),
    }

    assert len(keys) == 4


def test_serialization_round_trip_preserves_fields() -> None:
    slot = _slot()

    payload = serialize_availability_slots([slot])
    restored = deserialize_availability_slots(payload)

    assert restored == [slot]
    assert restored[0].id == slot.id
    assert restored[0].price == Decimal("320.00")
    assert restored[0].starts_at == slot.starts_at
    assert restored[0].starts_at.tzinfo is not None


def test_serialization_preserves_empty_list() -> None:
    payload = serialize_availability_slots([])

    assert payload == b"[]"
    assert deserialize_availability_slots(payload) == []


def test_serialization_produces_readable_json() -> None:
    slot = _slot()

    payload = serialize_availability_slots([slot])

    assert payload.startswith(b"[{")
    assert b'"doctor_name"' in payload
    assert b"pickled" not in payload


def test_get_hit_returns_deserialized_slots() -> None:
    slot = _slot()
    client = MagicMock()
    client.get.return_value = serialize_availability_slots([slot])
    cache = _cache(client=client)

    result = cache.get(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
    )

    assert result == [slot]
    client.get.assert_called_once()


def test_get_miss_returns_none() -> None:
    client = MagicMock()
    client.get.return_value = None
    cache = _cache(client=client)

    result = cache.get(
        service_id=None,
        doctor_id=None,
        target_date=None,
    )

    assert result is None


def test_get_cached_empty_list_is_a_hit() -> None:
    client = MagicMock()
    client.get.return_value = "[]"
    cache = _cache(client=client)

    result = cache.get(
        service_id=SERVICE_A,
        doctor_id=None,
        target_date=None,
    )

    assert result == []


def test_get_fails_open_on_redis_error() -> None:
    client = MagicMock()
    client.get.side_effect = RedisConnectionError("redis down")
    cache = _cache(client=client)

    result = cache.get(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
    )

    assert result is None


def test_get_fails_open_on_os_error() -> None:
    client = MagicMock()
    client.get.side_effect = ConnectionError("connection refused")
    cache = _cache(client=client)

    result = cache.get(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
    )

    assert result is None


def test_get_treats_invalid_payload_as_miss() -> None:
    client = MagicMock()
    client.get.return_value = "not-valid-json{{"
    cache = _cache(client=client)

    result = cache.get(
        service_id=SERVICE_A,
        doctor_id=None,
        target_date=None,
    )

    assert result is None


def test_set_writes_json_with_ttl() -> None:
    slot = _slot()
    client = MagicMock()
    cache = _cache(
        client=client,
        jitter_fn=lambda: 0,
    )

    cache.set(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
        slots=[slot],
    )

    args, kwargs = client.set.call_args
    expected_key = build_availability_cache_key(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
    )
    assert args[0] == expected_key
    assert args[1] == serialize_availability_slots([slot])
    assert kwargs == {"ex": 30}


def test_set_fails_open_on_redis_error() -> None:
    client = MagicMock()
    client.set.side_effect = RedisConnectionError("redis down")
    cache = _cache(client=client)

    cache.set(
        service_id=SERVICE_A,
        doctor_id=None,
        target_date=None,
        slots=[],
    )

    client.set.assert_called_once()


def test_effective_ttl_without_jitter_is_base_ttl() -> None:
    cache = _cache(jitter_fn=lambda: 0)

    assert cache.effective_ttl_seconds() == 30


def test_effective_ttl_includes_maximum_jitter() -> None:
    cache = _cache(jitter_fn=lambda: 10)

    assert cache.effective_ttl_seconds() == 40


def test_effective_ttl_with_default_jitter_stays_in_bounds() -> None:
    cache = _cache()

    ttl = cache.effective_ttl_seconds()

    assert 30 <= ttl <= 40


def test_effective_ttl_with_zero_max_jitter_skips_randomness() -> None:
    cache = _cache(
        settings=_settings(
            availability_cache_ttl_jitter_seconds=0,
        ),
    )

    assert cache.effective_ttl_seconds() == 30


def test_invalidation_keys_cover_every_matching_variant() -> None:
    keys = build_availability_invalidation_keys(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        business_date=DAY_1,
    )

    assert len(keys) == 8
    assert len(set(keys)) == 8

    prefix = f"{AVAILABILITY_CACHE_NAMESPACE}:{AVAILABILITY_CACHE_VERSION}"
    service_part = str(SERVICE_A)
    doctor_part = str(DOCTOR_A)
    date_part = DAY_1.isoformat()

    for service_filter in (service_part, ALL_FILTER):
        for doctor_filter in (doctor_part, ALL_FILTER):
            for date_filter in (date_part, ALL_FILTER):
                assert (
                    f"{prefix}:{service_filter}:{doctor_filter}:{date_filter}"
                    in keys
                )


def test_invalidate_deletes_all_variants_after_converting_timezone() -> None:
    client = MagicMock()
    client.delete.return_value = 3
    cache = _cache(client=client)

    # 01:00 UTC on Apr 12 is 22:00 on Apr 11 in America/Sao_Paulo.
    cache.invalidate_for_appointment(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        starts_at=datetime(
            2027,
            4,
            12,
            1,
            0,
            tzinfo=UTC,
        ),
    )

    args, _ = client.delete.call_args
    assert len(args) == 8
    assert all(":2027-04-11" in key or ":all" in key for key in args)
    assert any(":2027-04-11" in key for key in args)


def test_invalidate_assumes_utc_for_naive_datetimes() -> None:
    client = MagicMock()
    client.delete.return_value = 8
    cache = _cache(client=client)

    # 01:00 treated as UTC is 22:00 on the previous day in
    # America/Sao_Paulo, which isolates the naive-as-UTC branch.
    cache.invalidate_for_appointment(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        starts_at=datetime(2027, 4, 12, 1, 0),  # noqa: DTZ001 -- naive input is the case under test
    )

    args, _ = client.delete.call_args
    assert any(":2027-04-11" in key for key in args)
    assert not any(":2027-04-12" in key for key in args)


def test_invalidate_fails_open_on_redis_error() -> None:
    client = MagicMock()
    client.delete.side_effect = RedisConnectionError("redis down")
    cache = _cache(client=client)

    cache.invalidate_for_appointment(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        starts_at=datetime(
            2027,
            4,
            12,
            13,
            0,
            tzinfo=UTC,
        ),
    )

    client.delete.assert_called_once()


def test_invalidate_fails_open_on_unexpected_error() -> None:
    client = MagicMock()
    client.delete.side_effect = RuntimeError("unexpected")
    cache = _cache(
        client=client,
        settings=_settings(
            business_timezone="Not/A_Timezone",
        ),
    )

    cache.invalidate_for_appointment(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        starts_at=datetime(
            2027,
            4,
            12,
            13,
            0,
            tzinfo=UTC,
        ),
    )

    client.delete.assert_not_called()


def test_disabled_cache_bypasses_client_operations() -> None:
    client = MagicMock()
    cache = _cache(
        client=client,
        settings=_settings(
            availability_cache_enabled=False,
        ),
    )

    assert cache.enabled is False
    assert (
        cache.get(
            service_id=SERVICE_A,
            doctor_id=DOCTOR_A,
            target_date=DAY_1,
        )
        is None
    )
    cache.set(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        target_date=DAY_1,
        slots=[],
    )
    cache.invalidate_for_appointment(
        service_id=SERVICE_A,
        doctor_id=DOCTOR_A,
        starts_at=datetime(
            2027,
            4,
            12,
            13,
            0,
            tzinfo=UTC,
        ),
    )

    client.get.assert_not_called()
    client.set.assert_not_called()
    client.delete.assert_not_called()


def test_cache_without_client_is_disabled() -> None:
    cache = _cache(client=None)

    assert cache.enabled is False
    assert (
        cache.get(
            service_id=None,
            doctor_id=None,
            target_date=None,
        )
        is None
    )


def test_create_redis_client_returns_none_when_disabled() -> None:
    settings = _settings(
        availability_cache_enabled=False,
    )

    assert create_redis_client(settings) is None


def test_create_redis_client_returns_redis_when_enabled() -> None:
    settings = _settings(
        redis_host="10.0.0.5",
        redis_port=6380,
        redis_db=2,
        redis_socket_timeout=1.5,
        redis_connect_timeout=0.5,
    )

    client = create_redis_client(settings)

    assert isinstance(client, Redis)
    assert client.connection_pool.connection_kwargs["host"] == "10.0.0.5"
    assert client.connection_pool.connection_kwargs["port"] == 6380
    assert client.connection_pool.connection_kwargs["db"] == 2
    assert (
        client.connection_pool.connection_kwargs["socket_timeout"] == 1.5
    )
    assert (
        client.connection_pool.connection_kwargs["socket_connect_timeout"]
        == 0.5
    )
    client.close()


def test_filter_log_fields_stringifies_identifiers() -> None:
    fields = _filter_log_fields(
        service_id=SERVICE_A,
        doctor_id=None,
        target_date=DAY_1,
    )

    assert fields == {
        "service_id": str(SERVICE_A),
        "doctor_id": None,
        "date": "2027-04-12",
    }
