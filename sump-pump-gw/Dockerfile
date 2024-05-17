# syntax=docker/dockerfile:1

FROM python:3.9

# Install GTK libraries
# RUN apt-get update && apt-get install -y libgtk-3-dev && \
#     rm -rf /var/lib/apt/lists/*
    
# RUN apt-get update && \
#     apt-get install -y libgirepository1.0-dev libcairo2-dev


WORKDIR /opt/app/sump-pump-gateway

COPY ./shared /opt/app/sump-pump-gateway/shared

COPY ./sump-pump-gw /opt/app/sump-pump-gateway

COPY ./sump-pump-gw/requirements.txt requirements.txt

RUN pip install --upgrade pip setuptools

RUN pip install --no-cache-dir -r requirements.txt

#RUN pip install --no-cache-dir -r requirements.txt


CMD ["python", "app.py"]