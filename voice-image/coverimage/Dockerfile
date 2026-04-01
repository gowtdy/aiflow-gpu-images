FROM aiflowbase:0.4

#ENV DEBIAN_FRONTEND=noninteractive

USER root
# 安装系统依赖

# 复制项目文件（chown 由 base entrypoint 在 run 時依 AIGC_UID/AIGC_GID 處理）
RUN rm -rf /app/*
COPY build_assets/ /app/

# 复制 fairseq 到镜像中（如果存在的话）
#RUN mkdir -p /app/fairseq
#COPY fairseq/ /app/fairseq/

RUN mkdir -p /app/log /app/output /app/assets/rmvpe  /app/assets/hubert  /app/models/service_models /app/models/service_model/common_models
RUN mkdir -p /app/data /app/data/uploads /app/data/middle /app/data/final /app/data/sepaudio /app/data/sepvocal /app/data/sepinstrum

# 安装 Python 依赖（root 安裝到系統路徑，不依賴 /home/aigc/.local）
#RUN pip install git+https://github.com/One-sixth/fairseq.git
RUN python3 -m pip install cython numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -v --no-build-isolation /app/fairseq

# 安装 Python 依赖
RUN python3 -m pip install --upgrade pip "pip<24.1" -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && python3 -m pip install -v -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#RUN python3 -m pip install --use-pep517 flash-attn -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 使用 base 的 ENTRYPOINT ["/entrypoint.sh"]，僅設 CMD；cover-worker 會覆蓋 CMD
CMD ["tail", "-f", "/dev/null"]
