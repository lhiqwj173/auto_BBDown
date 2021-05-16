FROM mengkevin/python:3.8-slim-buster

LABEL maintainer="lhiiqwj"

COPY . /app
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg wget && \
        cd /app && \
        wget -O - https://github.com/nilaoda/BBDown/releases/download/1.3.8/BBDown_v1.3.8_20210330_linux_x64.tar.gz | tar xz && \
        chmod +x BBDown && \
        mkdir log && \
        pip install --no-cache-dir -r requirements.txt && \
        apt-get purge -y wget && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*
VOLUME ["/app/config", "/app/downloads"]

CMD ["python", "run.py"]
