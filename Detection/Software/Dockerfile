FROM python:3.11.3-slim
LABEL authors="rodr"

ADD . /software
WORKDIR ./software

RUN pip install poetry

RUN poetry install

ENV PORT=8000

EXPOSE $PORT

CMD ["bash", "-c", "poetry run uvicorn software.API.FastAPI.BeltDrainLLE.BeltDrainLLE:app --port $PORT --host 0.0.0.0 > /home/output.txt"]