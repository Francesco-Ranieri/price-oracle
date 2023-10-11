FROM bitnami/spark:3.5.0-debian-11-r0

# USER root
# RUN apt update && \
#     apt upgrade -y && \
#     apt-get install wget build-essential libreadline-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev -y && \
#     wget -c https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tar.xz && \
#     tar -xf Python-3.10.0.tar.xz && \
#     cd Python-3.10.0 && \
#     ./configure --enable-optimizations && \
#     make altinstall
# ENV PYSPARK_PYTHON=/usr/local/bin/python3.10