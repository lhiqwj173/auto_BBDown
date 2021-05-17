FROM python:3.8-slim-buster
#FROM mengkevin/python:3.8-slim-buster

LABEL maintainer="lhiiqwj"

ENV TZ=Asia/Shanghai

COPY . /app
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg wget && \
        ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
        cd /app && \
        wget -O - https://github.com/nilaoda/BBDown/releases/download/1.3.8/BBDown_v1.3.8_20210330_linux_x64.tar.gz | tar xz && \
        chmod +x BBDown && \
        pip install --no-cache-dir -r requirements.txt && \
        apt-get purge -y wget && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*
VOLUME ["/app/config", "/app/downloads"]

#CMD ["python", "run.py"]
