FROM bitnami/spark:3.5.0-debian-11-r0

# Install python3.9
RUN apt-get update && apt-get install -y python3.9 python3-pip
ENV PYSPARK_PYTHON=/usr/bin/python3.9