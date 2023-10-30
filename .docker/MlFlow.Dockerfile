FROM bitnami/mlflow:2.7.1-debian-11-r0

COPY mlflow/memory /app/:memory
USER root
RUN chmod 777 /app
RUN chmod 777 /app/:memory