import inspect

try:
    import asyncmq
    from asyncmq.backends.postgres import PostgresBackend

    print(f"AsyncMQ file: {asyncmq.__file__}")
    print(f"PostgresBackend file: {inspect.getfile(PostgresBackend)}")

    # Try to read the PostgresBackend source
    with open(inspect.getfile(PostgresBackend), "r") as f:
        content = f.read()
        if (
            "CREATE TABLE" in content
            or "init_db" in content
            or "ensure_tables" in content
        ):
            print("Found potential table creation code in PostgresBackend source.")
            print(content)
        else:
            print("No obvious table creation code found in PostgresBackend source.")

except ImportError as e:
    print(f"Could not import asyncmq: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
