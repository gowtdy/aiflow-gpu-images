# 转写基础镜像设计（whisper / parakeet / funasr）

- 日期：2026-10-04
- 分支：`feature/srt`
- 状态：待评审

## 1. 背景与目标

构建三个语音转写基础 Docker 镜像，分别基于 whisper、parakeet、funasr，供上层灵活 `FROM` 依赖实现转写逻辑。

定位为**纯基础环境**：只装框架 + 依赖 + 约定权重挂载路径，**不包含任何转写业务逻辑**。继承仓库 base 镜像的 `/entrypoint.sh`（运行时按 `AIGC_UID/AIGC_GID` 切换 `aigc` 用户），`CMD` 保持 `tail -f /dev/null`，上层覆盖 `CMD` 即可。

线上有两类 GPU：

| 显卡 | 架构 | base 镜像 |
|------|------|-----------|
| RTX 50 系列 | Blackwell（sm_120） | `gpu50-baseimage:0.2`（pytorch 2.11.0 / CUDA 12.8） |
| V100 系列 | Volta（sm_70） | `aiflowbase:0.4`（pytorch 2.4.1 / CUDA 12.1） |

两个 base 各管各的架构，**不需要 cross-compat**（明确不要求 `gpu50-baseimage` 兼容 sm_70 kernel）。

## 2. 关键决策

| 项 | 决策 |
|----|------|
| whisper 实现 | **faster-whisper**（`pip install faster-whisper`，CTranslate2 后端） |
| parakeet 模型 | **Parakeet-TDT-0.6B-v3**（NVIDIA NeMo 生态，NeMo / open-nemo 加载） |
| funasr 模型 | **paraformer-zh**（阿里 FunASR，`pip install funasr`） |
| 整体结构 | 三个独立镜像，各自 Dockerfile（方案 A） |
| base 切换 | Dockerfile `ARG BASE_IMAGE` + 每镜像两个 build 脚本（V100 / RTX50）+ `version.txt` |
| 权重处理 | 运行时 volume 挂载到 `/app/models/`，**不 bake 进镜像** |
| 镜像定位 | 纯基础环境，`CMD ["tail","-f","/dev/null"]` |

## 3. 目录结构

```
voice-image/transcribe-image/
├── whisper-transcribe-image/
│   ├── Dockerfile
│   ├── version.txt
│   ├── build-whisper-v100-image.sh
│   ├── build-whisper-rtx50-image.sh
│   ├── start-whisper-v100-image.sh
│   ├── start-whisper-rtx50-image.sh
│   ├── stop-whisper-image.sh
│   ├── docker-compose.yml
│   └── build_assets/
│       └── requirements.txt
├── parakeet-transcribe-image/
│   ├── Dockerfile
│   ├── version.txt
│   ├── build-parakeet-v100-image.sh
│   ├── build-parakeet-rtx50-image.sh
│   ├── start-parakeet-v100-image.sh
│   ├── start-parakeet-rtx50-image.sh
│   ├── stop-parakeet-image.sh
│   ├── docker-compose.yml
│   └── build_assets/
│       └── requirements.txt
└── funasr-transcribe-image/
    ├── Dockerfile
    ├── version.txt
    ├── build-funasr-v100-image.sh
    ├── build-funasr-rtx50-image.sh
    ├── start-funasr-v100-image.sh
    ├── start-funasr-rtx50-image.sh
    ├── stop-funasr-image.sh
    ├── docker-compose.yml
    └── build_assets/
        └── requirements.txt
```

## 4. base 切换机制

每个 Dockerfile 首行参数化 base，默认 `aiflowbase:0.4`（仅作直接 `docker build` 时的 fallback）：

```dockerfile
ARG BASE_IMAGE=aiflowbase:0.4
FROM ${BASE_IMAGE}
```

每个镜像两个 build 脚本，base 与 tag 均硬编码，版本号从 `version.txt` 读取：

```bash
# build-whisper-v100-image.sh
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t whisper-transcribe-image:v100-$VER \
    --build-arg BASE_IMAGE=aiflowbase:0.4 -f Dockerfile .

# build-whisper-rtx50-image.sh
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t whisper-transcribe-image:rtx50-$VER \
    --build-arg BASE_IMAGE=gpu50-baseimage:0.2 -f Dockerfile .
```

要点：

- **tag 必须区分 base**（`v100-$VER` vs `rtx50-$VER`），避免同名 tag 第二次 build 覆盖第一次。
- **每镜像一个 `version.txt`**，三个镜像版本独立演进，不做顶层共享。
- 脚本路径下永远显式传 `--build-arg`，消除「忘记传参、错落到默认 base」的风险。

tag 约定：`<image>:<base>-<version>`，如 `whisper-transcribe-image:v100-0.1`、`whisper-transcribe-image:rtx50-0.1`。

## 5. 依赖安装

| 镜像 | 安装方式 | 跨 base 风险 |
|------|----------|--------------|
| whisper | `pip install faster-whisper`（自带 ctranslate2 / tokenizers / onnxruntime / av / huggingface_hub） | 低，几乎不绑 torch |
| funasr | `pip install funasr`（自带 modelscope / torchaudio 等） | 中，torch 约束较宽 |
| parakeet | NeMo 全家桶（`nemo_toolkit` 或 `open-nemo`，具体包名待实现时定）加载 Parakeet-TDT-0.6B-v3 | **高**，NeMo 对 torch 版本约束最紧 |

所有 pip 安装沿用仓库一致的两套镜像源（`mirrors.aliyun.com` 或 `pypi.tuna.tsinghua.edu.cn`）。

## 6. 权重处理（默认全 mount）

三个模型权重均**不在 build 时下载**，运行时通过 volume 挂载到 `/app/models/<模型名>`：

| 镜像 | 权重 |
|------|------|
| whisper | `Systran/faster-whisper-large-v3`（CTranslate2 格式） |
| parakeet | `nvidia/parakeet-tdt-0.6b-v3` |
| funasr | paraformer-zh（FunASR / modelscope 布局） |

理由：基础镜像保持轻量、可复用；三套权重体积大（约 1GB / 2.4GB / 3GB），bake 会显著膨胀镜像且不利于上层切换模型规格。换一个挂载目录即可换模型，无需改镜像。

## 7. build 与运行

### 7.1 运行定位

docker-compose.yml 仅用于**本地冒烟验证**，不是线上编排；线上 GPU 分配由上层编排决定。

### 7.2 docker-compose 样貌（以 whisper 为例）

```yaml
services:
  whisper-transcribe:
    image: whisper-transcribe-image:${IMG_TAG:-v100-0.1}   # 值由 start-whisper-{v100,rtx50}-image.sh 传入
    hostname: whisper-transcribe
    container_name: whisper-transcribe
    restart: unless-stopped
    network_mode: host
    dns: [8.8.8.8, 1.1.1.1, 192.168.3.1]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['2']          # 本地调试示例，按机器 GPU 编号改
              capabilities: [gpu]
    environment:
      - AIGC_UID=${AIGC_UID:-1001}
      - AIGC_GID=${AIGC_GID:-1001}
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - NVIDIA_REQUIRE_CUDA=cuda>=12.0
      - TZ=Asia/Shanghai
    volumes:
      - /path/to/faster-whisper-large-v3:/app/models/faster-whisper-large-v3
      - /home/aigc/data/aioutput/logs:/app/log
    extra_hosts:
      - host.docker.internal:host-gateway
```

parakeet / funasr 结构一致，差异仅 image 名、container 名、模型 volume。

### 7.3 冒烟验证（每个镜像 build 后的交付标准）

```bash
docker run --gpus all -it --rm whisper-transcribe-image:v100-0.1 \
    python3 -c "import faster_whisper; print(faster_whisper.__version__)"
```

三件套分别为 `import faster_whisper` / `import nemo.collections.asr` / `import funasr`，再 `nvidia-smi` 确认 GPU 可见；有 mount 权重时加跑一次最小转写确认模型可加载推理。

### 7.4 start / stop 脚本（本地起停）

沿用仓库 start/stop 惯例（对齐 host `aigc` 用户后 `docker compose up/down`）。start 按 base 拆两个、tag 硬编码；stop 只 `down`、不依赖 base，保留一个：

```bash
# start-whisper-v100-image.sh
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="v100-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d

# start-whisper-rtx50-image.sh
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="rtx50-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d

# stop-whisper-image.sh
docker compose -f docker-compose.yml down
```

docker-compose 的 image 用变量引用（值由 start 脚本硬编码传入，无外部传参）：

```yaml
image: whisper-transcribe-image:${IMG_TAG:-v100-0.1}
```

parakeet / funasr 类推。

## 8. 每个镜像交付物

- `Dockerfile`
- `version.txt`
- 两个 build 脚本（`build-<name>-v100-image.sh` / `build-<name>-rtx50-image.sh`）
- `start-<name>-v100-image.sh` / `start-<name>-rtx50-image.sh` / `stop-<name>-image.sh`
- `docker-compose.yml`
- `build_assets/requirements.txt`

parakeet / funasr 视 `[待验证]` 结果，可能额外各加一个 `constraints.txt` 用于按 base 分叉依赖。

## 9. 待验证项

实现阶段在 V100 / RTX 50 上各实测一次，结果决定 requirements 是否需按 base 分叉：

1. **NeMo（parakeet）在 pytorch 2.4.1 与 2.11.0 下各自可用的版本组合** —— 三个里最大风险；若两版 torch 不共用同一 NeMo 版本，该镜像 requirements 需按 base 分叉（两套约束，条件安装）。
   - **V100（torch 2.4.1）实测：** `nemo_toolkit[asr]==2.6.1` + `numpy<2` 可用（2.6.2+ 要求 torch≥2.6.0，3.0.0 要求 torch 2.14/CUDA 13；`numpy<2` 保住 base 的 numpy 1.26.4 供 dctorch）。**RTX 50（torch 2.11.0）待验** —— 2.6.1 是否兼容 torch 2.11，或需升 2.6.2+，若不适配则 requirements 按 base 分叉。
2. **ctranslate2 对 CUDA 12.1（V100）与 12.8 / sm_120（RTX 50）的版本覆盖** —— 能否单一版本两 base 通用。
   - **V100（CUDA 12.1 / sm_70）实测：** ctranslate2 4.8.2 单 wheel 可用。**RTX 50（CUDA 12.8 / sm_120）待验。**
3. **funasr / torchaudio 在两个 torch 版本上的兼容** —— 风险较低，大概率一版通用。
   - **V100（torch 2.4.1）实测：** funasr 1.4.16 安装成功、可导入。**RTX 50（torch 2.11.0）待验。**