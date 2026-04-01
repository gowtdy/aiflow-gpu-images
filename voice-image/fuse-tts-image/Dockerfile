FROM aiflowbase:0.4

#ENV DEBIAN_FRONTEND=noninteractive

USER root
# 安装系统依赖
# RUN apt-get update && apt-get install -y libavutil-dev libavcodec-dev libavformat-dev rsync openssh-client

# 复制项目文件（chown 由 base entrypoint 在 run 時依 AIGC_UID/AIGC_GID 處理）
RUN rm -rf /app/*
COPY build_assets/ /app/

ENV PYTHONUNBUFFERED=1

# 安装 Python 依赖（root 安裝到系統路徑，不依賴 /home/aigc/.local）
RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && python3 -m pip install -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && python3 -m pip install /app/LangSegment-0.3.5-py3-none-any.whl -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -f /app/LangSegment-0.3.5-py3-none-any.whl

#RUN python3 -m pip install --use-pep517 flash-attn -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 使用 base 的 ENTRYPOINT ["/entrypoint.sh"]，僅設 CMD；tts-worker 會覆蓋 CMD
CMD ["tail", "-f", "/dev/null"]
