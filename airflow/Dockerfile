# Use the official Apache Airflow image as the base image
FROM apache/airflow:2.7.1-python3.11 AS base

COPY requirements.txt /
# Install additional Python packages using pip
# NOTE: In the example below, we also add apache-airflow package to be installed - in the very same version that the image  
# version you used it from. This is not strictly necessary, but it is a good practice to always install the same version of 
# apache-airflow as the one you are using. This way you can be sure that the version you are using is the same as the one you 
# are extending. In some cases where your new packages have conflicting dependencies, pip might decide to downgrade or upgrade 
# apache-airflow for you, so adding it explicitly is a good practice - this way if you have conflicting requirements, you will 
# get an error message with conflict information, rather than a surprise downgrade or upgrade of airflow. If you upgrade 
# airflow base image, you should also update the version to match the new version of airflow.0
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

COPY dags dags
COPY assets assets