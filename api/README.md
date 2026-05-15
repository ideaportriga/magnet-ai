## Install

### Developer environment

- Install [Python 3.12](https://www.python.org/).
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package & project manager.
- Visual C++ Redistributable (optional) - you should install it if you get explicit errors about it during installation.

### Install

From the `api/` directory run `uv sync`.
It will create `.venv/`, install all locked dependencies, and provision a Python interpreter for the project.

### Virtual environment

`uv sync` puts the venv at `./.venv`. Activate it if you prefer to run commands directly:
```
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
```

### Executing commands

If the virtual environment is activated - just execute the command/script, for example:
```
python some_script.py
uvicorn app:app
pytest
```

Otherwise - prefix commands with `uv run` to execute inside the project's virtualenv:
```
uv run python some_script.py
uv run uvicorn app:app
uv run pytest
```


### Running the application

Create `.env` file based on `.env.example`.
Run app from src directory.

With default parameters:
```
uv run uvicorn app:app --env-file="../.env"
```

In reload mode:
```
uv run uvicorn app:app --env-file="../.env" --reload
```

In a different port:
```
uv run uvicorn app:app --env-file="../.env" --port="8001"
```

### Dockerized

Dockerfile allows to build Docker image an run application as a Docker container

#### Special requirements

Variables in env file cannot contain newlines
Variables should be without quotes

#### Build
Build image:
```
docker build -t ai-bridge:<tag> .
```

#### Run

```
docker run -d -p 8000:9000 --env-file=.env --name ai-bridge ai-bridge:<tag>
```

#### Formatting

TBD

#### Linting

Run the Ruff linter over the project:

```
uv run ruff check
```

with automatic issue resolving:

```
uv run ruff check --fix
```



#### Testing

**NB: Some of the tests are skipped as they are currently broken. Fixing is in progress.**

To run tests:
```
uv run pytest

# Or if virtual env is activated just:
pytest
```

Tests are using different env file - `.env.test` which should not contain any access data to ensure that no real external services (Chroma, OpenAI) are called.

##### Capturing output
To show print output in the output use command-line option `-s`:

```
uv run pytest -s
```
[How to capture stdout/stderr output](https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html)


##### Select tests
To select tests use command-line option `-k`:

Example:
```
uv run pytest -k stores
```
[Using -k expr to select tests based on their name](https://docs.pytest.org/en/7.1.x/example/markers.html#using-k-expr-to-select-tests-based-on-their-name)

## JSONB columns and serialization

**Rule:** never call `json.dumps()` manually before handing a value to a JSONB
column. Let SQLAlchemy's engine-level `json_serializer_for_sqlalchemy`
(`core/config/base.py`) handle it — it is idempotent, uses `litestar`'s
encoder (msgspec/orjson), and handles `datetime`/`UUID`/`Decimal` natively.

### ORM columns

Declare JSONB columns with `advanced_alchemy.types.JsonB`:

```python
from advanced_alchemy.types import JsonB

variants: Mapped[Optional[list[Any]]] = mapped_column(JsonB, nullable=True)
```

Assign Python `dict` / `list` directly. Do **not** pre-serialize.

### Raw SQL with `text()`

When you can't avoid raw SQL (dynamic table names, COALESCE-merge semantics),
declare the JSONB bind param explicitly:

```python
from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

stmt = text(
    f"""
    UPDATE {table}
    SET metadata = CASE
        WHEN :metadata_json IS NULL THEN metadata
        ELSE COALESCE(metadata, '{{}}'::jsonb) || :metadata_json
    END
    WHERE id = :id
    """
).bindparams(bindparam("metadata_json", type_=PG_JSONB(none_as_null=True)))

await db_session.execute(
    stmt, {"id": doc_id, "metadata_json": payload_dict_or_None}
)
```

`none_as_null=True` is important — it maps Python `None` to SQL `NULL`
(otherwise JSON `null` is stored and `IS NULL` checks silently fail).

### What to avoid

- `json.dumps(payload, default=str)` + `CAST(:x AS jsonb)` — legacy pattern
  that caused double-encoding; fixed by the one-shot
  `scripts/fix_jsonb_strings.py`.
- Re-implementing a custom `TypeDecorator` for JSONB — use `JsonB` from
  `advanced_alchemy.types`.
