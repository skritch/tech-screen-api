# About

This is a simple API for artists and albums, using FastAPI, SQLModel, and SQLite.


## Install

Set up a Python 3 environment, e.g. with: 
```
python3 -m venv .virtualenv
source .virtualenv/bin/activate
```

Then install requirements:
```
pip install -r requirements.txt
```

(Test requirements are currently mixed in.)

## Running the API

Set up environment variables based on `.env.sample`, e.g. with `export $(cat .env | xargs)`.

```
uvicorn src.api:app
```

Use `--reload` for development and `--port` to change the serving port.

A swagger UI is served at `http://localhost:8000/docs` (by default), and can be used to 
make test queries.


## Testing

Test with pytest using an in-memory SQLite:
```
pytest -v
```
