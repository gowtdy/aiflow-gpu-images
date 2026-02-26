FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-devel AS builder

ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（以 root 用户执行）
#RUN apt-get update && apt-get install -y software-properties-common telnet net-tools\
#    && add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 \
#    && apt-get update \
#    && apt-get install -y ffmpeg libavutil-dev libavcodec-dev libavformat-dev libavdevice-dev libavfilter-dev libswscale-dev libswresample-dev wget vim rsync openssh-client git

RUN apt update && apt install -y \
    autoconf automake build-essential cmake git-core libass-dev \
    libfreetype6-dev libsdl2-dev libtool libva-dev libvdpau-dev \
    libvorbis-dev libxcb1-dev libxcb-shm0-dev libxcb-xfixes0-dev \
    pkg-config texinfo wget yasm nasm zlib1g-dev \
    libx264-dev libx265-dev libnuma-dev libvpx-dev \
    libfdk-aac-dev libmp3lame-dev libopus-dev \
    libaom-dev libwebp-dev libssl-dev \
    meson ninja-build \
    nvidia-cuda-toolkit

WORKDIR /tmp
RUN git clone --depth 1 --branch v2.3.0 https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
    cd SVT-AV1/Build && \
    cmake .. -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/SVT-AV1

WORKDIR /tmp
RUN git clone --depth 1 https://code.videolan.org/videolan/dav1d.git && \
    cd dav1d && \
    meson setup build --buildtype release --prefix=/usr/local --libdir=lib && \
    meson compile -C build && \
    meson install -C build && \
    ldconfig && \
    cd / && rm -rf /tmp/dav1d

# 安装 ffnvcodec（NVIDIA FFmpeg 编解码器头文件）
WORKDIR /tmp
RUN git clone --depth 1 https://git.videolan.org/git/ffmpeg/nv-codec-headers.git && \
    cd nv-codec-headers && \
    make install && \
    cd / && rm -rf /tmp/nv-codec-headers

# 复制项目文件
COPY build_assets/ /app/

#RUN pkg-config --modversion SvtAv1Enc
ENV CUDA_PATH=/usr/local/cuda

WORKDIR /app
RUN tar xvf ffmpeg-8.0.1.tar.xz
WORKDIR /app/ffmpeg-8.0.1
RUN ./configure \
    --prefix=/opt/ffmpeg \
    --extra-cflags="-I${CUDA_PATH}/include" \
    --extra-ldflags="-L${CUDA_PATH}/lib64" \
    --extra-libs="-lpthread -lm" \
    --enable-gpl \
    --enable-nonfree \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libvpx \
    --enable-libfdk-aac \
    --enable-libmp3lame \
    --enable-libopus \
    --enable-libass \
    --enable-libsvtav1 \
    --enable-libaom \
    --enable-cuda \
    --enable-nvenc \
    --enable-libnpp \
    --enable-libdav1d \
    --enable-libwebp \
    --enable-openssl \
    --enable-shared \
    --disable-debug \
    --disable-sndio \
    --disable-doc

RUN make -j$(nproc)
RUN make install

# 将 dav1d 库复制到 ffmpeg 的 lib 目录
RUN if [ -f /usr/local/lib/libdav1d.so.7 ]; then \
        cp -v /usr/local/lib/libdav1d.so* /opt/ffmpeg/lib/ && \
        ls -la /opt/ffmpeg/lib/libdav1d.so* && \
        echo "libdav1d copied successfully"; \
    else \
        echo "Error: libdav1d.so.7 not found in /usr/local/lib" && \
        find /usr/local -name "libdav1d.so*" 2>/dev/null && \
        exit 1; \
    fi

#--------- runtime image ---------
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-devel

# 安装 ffmpeg 运行时依赖
RUN apt-get update && apt-get install -y \
    # libdrm 相关
    libdrm2 \
    libdrm-common \
    # libxcb 相关（X11 支持）
    libxcb1 \
    libxcb-shm0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-render0 \
    libxcb-randr0 \
    libxcb-sync1 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-util1 \
    libxcb-xkb1 \
    libxcb-dri2-0 \
    libxcb-dri3-0 \
    libxcb-present0 \
    libxcb-glx0 \
    # X11 Video 扩展
    libxv1 \
    # 音频库
    libasound2 \
    # 视频加速相关
    libva2 \
    libva-drm2 \
    libva-x11-2 \
    libvdpau1 \
    # 编解码器运行时库（根据 ldd 输出确定版本）
    libx264-163 \
    libx265-199 \
    libvpx7 \
    libfdk-aac2 \
    libmp3lame0 \
    libopus0 \
    libaom3 \
    libwebp7 \
    libwebpmux3 \
    # libass 相关（字幕支持）
    libass9 \
    libfreetype6 \
    libfontconfig1 \
    libfribidi0 \
    libharfbuzz0b \
    # OpenSSL（加密支持）
    libssl3 \
    # 其他可能需要的库
    libnuma1 \
    libvorbis0a \
    libvorbisenc2 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/ffmpeg /opt/ffmpeg

# 创建用户 aigc，指定UID和GID为1001以匹配宿主机
# 宿主机的账号 aigc的id为 1001 调整为一致， 确保 aigc 用户有正确的 UID/GID (1001:1001)，这样文件所有者会显示为用户名而不是数字
# id aigc可以查看账号的id
RUN groupadd -g 1001 aigc && useradd -m -s /bin/bash -u 1001 -g 1001 aigc

# 复制项目文件
COPY build_assets/ /app/
RUN chown -R aigc:aigc /app
WORKDIR /app

# 设置Python用户安装路径到PATH
ENV PATH="/home/aigc/.local/bin:/opt/ffmpeg/bin:$PATH"
ENV LD_LIBRARY_PATH="/opt/ffmpeg/lib:/usr/local/lib:$LD_LIBRARY_PATH"

# 切换到 aigc 用户
USER aigc



# 需要先手动下载一下 flash-attn， wget  https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.4cxx11abiFALSE-cp311-cp311-linux_x86_64.whl

RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
  && python3 -m pip install flash_attn-2.7.4.post1+cu12torch2.4cxx11abiFALSE-cp311-cp311-linux_x86_64.whl \
  && python3 -m pip install -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


#ENTRYPOINT ["python"]
CMD ["tail", "-f", "/dev/null"]
