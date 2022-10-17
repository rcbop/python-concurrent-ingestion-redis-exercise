FROM --platform=amd64 python:3.8-alpine

WORKDIR /app

COPY common .
RUN pip install -e .
COPY s3mock .
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "s3_api_mock.py"]