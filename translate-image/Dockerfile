FROM aiflowbase:0.2

USER root

# 复制项目文件
RUN rm -rf /app/*
COPY build_assets/ /app/

RUN mkdir -p /app/log
RUN chown -R aigc:aigc /app/log
RUN chmod -R 755 /app/log

# 设置启动脚本权限（需要在 root 用户下执行）
RUN chmod +x /app/start_mt_server.sh

# 设置文件所有权并切换用户
RUN chown -R aigc:aigc /app
USER aigc

# 设置Python用户安装路径到PATH
ENV PATH="/home/aigc/.local/bin:$PATH"

RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
  && python3 -m pip install -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  && python3 -m pip install git+https://github.com/huggingface/transformers@4970b23cedaf745f963779b4eae68da281e8c6ca

WORKDIR /app

ENTRYPOINT ["tail", "-f", "/dev/null"]
#ENTRYPOINT ["./start_gn_upload_server.sh"]
