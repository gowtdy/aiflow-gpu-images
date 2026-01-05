FROM pytorch/pytorch:2.8.0-cuda12.6-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（以 root 用户执行）
RUN apt-get update && apt-get install -y software-properties-common telnet net-tools\
    && apt-get update \
    && apt-get install -y wget vim rsync openssh-client git

# 创建用户 aigc，指定UID和GID为1001以匹配宿主机
# 宿主机的账号 aigc的id为 1001 调整为一致， 确保 aigc 用户有正确的 UID/GID (1001:1001)，这样文件所有者会显示为用户名而不是数字
# id aigc可以查看账号的id
RUN groupadd -g 1001 aigc && useradd -m -s /bin/bash -u 1001 -g 1001 aigc

# 复制项目文件
COPY build_assets/ /app/
RUN chown -R aigc:aigc /app

# 切换到 aigc 用户
USER aigc
WORKDIR /app

# 设置Python用户安装路径到PATH
ENV PATH="/home/aigc/.local/bin:$PATH"

# 需要先手动下载一下 flash-attn， wget  https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.4cxx11abiFALSE-cp311-cp311-linux_x86_64.whl

RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
  && python3 -m pip install flash_attn-2.8.3+cu126torch2.8-cp311-cp311-linux_x86_64.whl \
  && python3 -m pip install -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#ENTRYPOINT ["python"]
CMD ["tail", "-f", "/dev/null"]
