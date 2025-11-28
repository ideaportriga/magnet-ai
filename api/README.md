## Install

### Developer environment

- Install [Python 3.12](https://www.python.org/).
- Install [Poetry 1.8](https://github.com/python-poetry/poetry) - tool for Python dependency management.
- Visual C++ Redistributable (optional) - you should install it if you get explicit errors about it during installation.
- Update Python packages with `python -m pip install -U pip wheel setuptools`

### Install

Once installed, from the project root directory run `poetry install`.
It will install `magnet-ai` project and its dependencies.

### Virtual environment

To activate virtual environment run [shell](https://python-poetry.org/docs/1.8/cli/#shell) command:
```
poetry shell
```
or:
```
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux
```

### Executing commands

If virtual environment is activated - just execute command/script, for example:
```
python some_script.py
uvicorn app:app
pytest
etc.

```

otherwise - use [run](https://python-poetry.org/docs/1.8/cli/#run) command - it will automatically execute your command inside the project's virtualenv:
```
poetry run python some_script.py
poetry run uvicorn app:app
poetry run pytest
etc.

```


### Running the application

Create `.env` file based on `.env.example`.
Run app from src directory.

With default parameters:
```
uvicorn app:app --env-file="../.env"
```

In reload mode:
```
uvicorn app:app --env-file="../.env" --reload
```

In a different port:
```
uvicorn app:app --env-file="../.env" --port="8001"
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
ruff check
```

with automatic issue resolving:

```
ruff check --fix
```



#### Testing

**NB: Some of the tests are skipped as they are currently broken. Fixing is in progress.**

To run tests:
```
poetry run pytest

# Or if virtual env is activated just:
pytest
```

Tests are using different env file - `.env.test` which should not contain any access data to ensure that no real external services (Chroma, OpenAI) are called.

##### Capturing output
To show print output in the output use command-line option `-s`:

```
poetry run pytest -s
```
[How to capture stdout/stderr output](https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html)


##### Select tests
To select tests use command-line option `-k`:

Example:
```
poetry run pytest -k stores
```
[Using -k expr to select tests based on their name](https://docs.pytest.org/en/7.1.x/example/markers.html#using-k-expr-to-select-tests-based-on-their-name)