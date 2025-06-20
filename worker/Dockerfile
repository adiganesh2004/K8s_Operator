FROM python:3.9-slim
WORKDIR /app
COPY worker.py .
RUN pip install pymongo
CMD ["python", "worker.py"]
