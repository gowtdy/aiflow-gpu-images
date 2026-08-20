FROM gpu50-baseimage:0.2
#FROM aiflowbase:0.4

#ENV DEBIAN_FRONTEND=noninteractive

USER root
# 安装系统依赖
# RUN apt-get update && apt-get install -y libavutil-dev libavcodec-dev libavformat-dev rsync openssh-client

# 复制项目文件（chown 由 base entrypoint 在 run 時依 AIGC_UID/AIGC_GID 處理）
RUN rm -rf /app/*
COPY build_assets/ /app/

RUN mkdir -p /app/index-tts/checkpoints /app/index-tts/models

# 安装 Python 依赖（root 安裝到系統路徑，不依賴 /home/aigc/.local）
# 钉死 setuptools<82：torch 2.11 需要；PIP_BUILD_CONSTRAINT 约束 unidic-lite 等 sdist 的隔离构建环境，
# 否则会拉到 setuptools 84 触发依赖冲突
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PIP_CONSTRAINT=/app/constraints.txt
ENV PIP_BUILD_CONSTRAINT=/app/constraints.txt

RUN python3 -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ \
    && python3 -m pip install "setuptools>=70,<82" wheel -i https://mirrors.aliyun.com/pypi/simple/ \
    && pip install --progress-bar=raw -v -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 给脚本执行权限
RUN chmod +x /app/start_index-tts.sh
# 使用 base 的 ENTRYPOINT ["/entrypoint.sh"]，僅設 CMD；tts-worker 會覆蓋 CMD
#CMD ["./start_index-tts.sh"]
CMD ["tail", "-f", "/dev/null"]