ARG BASE_IMAGE=aiflowbase:0.4
FROM ${BASE_IMAGE}

USER root

RUN rm -rf /app/*
COPY build_assets/ /app/

RUN mkdir -p /app/models /app/log

ENV PYTHONUNBUFFERED=1

RUN python3 -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ \
    && python3 -m pip install -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

CMD ["tail", "-f", "/dev/null"]