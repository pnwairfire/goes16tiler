FROM osgeo/gdal:ubuntu-small-3.2.2
MAINTAINER Stuart Illson

COPY ./requirements.txt requirements.txt

RUN apt-get update \
    && apt-get upgrade -y \
    && apt install -y wget openssl cmake python3-pip netcdf-bin awscli \
    && apt -y upgrade gdal-bin

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

RUN mkdir /app/
WORKDIR /app/
COPY ./goes16tiler /app/goes16tiler
COPY ./spatial_data /app/spatial_data
COPY ./tiles /app/tiles
COPY ./temp /app/temp