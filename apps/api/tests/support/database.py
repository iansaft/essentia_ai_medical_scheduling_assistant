from pathlib import Path

from psycopg import Connection, sql


def _up_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise RuntimeError(f"SQL directory does not exist: {directory}")

    files = sorted(directory.glob("*.up.sql"))
    if not files:
        raise RuntimeError(
            f"No '*.up.sql' files were found in {directory}. "
            "The integration tests expect golang-migrate style up migrations."
        )

    return files


def apply_up_sql(connection: Connection, directory: Path) -> None:
    for file_path in _up_files(directory):
        connection.execute(file_path.read_text(encoding="utf-8"))


def truncate_application_tables(connection: Connection) -> None:
    rows = connection.execute(
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename NOT IN ('schema_migrations', 'seed_migrations')
        ORDER BY tablename
        """
    ).fetchall()

    table_names = [row[0] for row in rows]
    if not table_names:
        raise RuntimeError("No application tables were found after migrations.")

    statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in table_names)
    )
    connection.execute(statement)


def reset_to_seed_state(connection: Connection, seeds_directory: Path) -> None:
    truncate_application_tables(connection)
    apply_up_sql(connection, seeds_directory)
