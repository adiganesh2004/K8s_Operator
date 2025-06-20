# watcher/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY watcher.py .

RUN pip install pymongo kubernetes

CMD ["python", "watcher.py"]
