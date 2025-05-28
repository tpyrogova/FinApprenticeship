FROM python:3.10-slim

# Install MLflow
RUN pip install --upgrade pip && \
    pip install mlflow

# Create directory for MLflow data
RUN mkdir -p /mlflow_data

# MLflow will run on port 5000 inside the container
EXPOSE 5000

WORKDIR /mlflow_data

# Start MLflow UI
CMD mlflow ui --host 0.0.0.0 --port 5000 --backend-store-uri file:/mlflow_data
