FROM gpu50-baseimage:0.1

#ENV DEBIAN_FRONTEND=noninteractive

USER root
# 安装系统依赖
# RUN apt-get update && apt-get install -y libavutil-dev libavcodec-dev libavformat-dev rsync openssh-client
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件（chown 由 base entrypoint 在 run 時依 AIGC_UID/AIGC_GID 處理）
RUN rm -rf /app/*
COPY build_assets/ /app/

RUN mkdir -p /app/weights/LongCat-Video-Avatar-1.5

# 安装 Python 依赖（root 安裝到系統路徑，不依賴 /home/aigc/.local）
RUN python3 -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

ENV PYTHONUNBUFFERED=1
# Lock torch to the CUDA build from gpu50-baseimage; stops transitive deps
# (e.g. audio-separator) from re-downloading a PyPI manylinux wheel.
RUN python3 -c "import torch; open('/tmp/constraints.txt', 'w').write(f'torch=={torch.__version__}\n')"
RUN pip install --progress-bar=raw -v -r requirements.txt -c /tmp/constraints.txt -i https://mirrors.aliyun.com/pypi/simple/
RUN pip install --progress-bar=raw -v -r requirements_avatar.txt -c /tmp/constraints.txt -i https://mirrors.aliyun.com/pypi/simple/

# 给脚本执行权限
#RUN chmod +x /app/start_index-tts.sh
# 使用 base 的 ENTRYPOINT ["/entrypoint.sh"]，僅設 CMD；tts-worker 會覆蓋 CMD
#CMD ["./start_index-tts.sh"]
CMD ["tail", "-f", "/dev/null"]