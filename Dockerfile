FROM python:3.12-slim

RUN pip install --no-cache-dir requests

WORKDIR /app
EXPOSE 8080

CMD ["python3", "-u", "/app/app.py"]
