FROM --platform=amd64 python:3.8-alpine

WORKDIR /app

COPY common .
RUN pip install -e .
COPY worker .
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]