# syntax=docker/dockerfile:1

FROM python:3.9

# Install GTK and D-Bus dependencies
# RUN apt-get update && apt-get install -y \
#     libgtk-3-dev \
#     libgirepository1.0-dev \
#     libcairo2-dev \
#     dbus \
#     && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y redis

WORKDIR /opt/app/sump-pump-serial

# COPY ./shared /opt/app//shared

# COPY ./sump-pump-serial/ /opt/app/

# COPY sump-pump-serial/requirements.txt requirements.txt

COPY ./shared /opt/app/sump-pump-serial/shared

COPY ./sump-pump-serial /opt/app/sump-pump-serial

COPY ./sump-pump-serial/requirements.txt requirements.txt

RUN pip install --upgrade pip setuptools

RUN pip install --no-cache-dir -r requirements.txt

# Run your Python application
CMD ["python", "py-serial.py"]