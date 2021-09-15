# Zageno URL shortening application (demo)

This is a small demonstration app that implements an API for shortening URLs.
It also returns a page to call the API.

The source is in the `src` directory.
Python code is in `src/app`.
HTML is in `src/static`.

To build, first install fastapi (the API framework) and uvicorn (the ASGI server implementation).
```
$ pip install fastapi
$ pip install uvicorn
```

Tests (such as pytest scripts) would go in the tests directory.
There are no tests there now (but some Python files have tests at the bottom that can be run as main).

The app can be run from the main directory by executing the `run.sh` shell script.
