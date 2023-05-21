FROM python:3.11.3-slim

RUN apt update && apt install git make

# requirements.txt is generated with pip-compile.
COPY requirements.txt /deps/requirements.txt

RUN python -m venv /deps/venv && . /deps/venv/bin/activate && pip install -r /deps/requirements.txt
