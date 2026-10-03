# 转写基础镜像（whisper / parakeet / funasr）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建三个语音转写基础 Docker 镜像（faster-whisper / Parakeet-TDT-0.6B-v3 / funasr-paraformer-zh），每个镜像可在 V100 与 RTX 50 两个 base 之间切换。

**Architecture:** 三个完全独立的镜像目录，各自 `FROM ${BASE_IMAGE}` 参数化 base；每个镜像两个 build 脚本 + 两个 start 脚本 + 一个 stop 脚本，版本号集中在各自的 `version.txt`。权重运行时挂载，不 bake。

**Tech Stack:** Docker、Python 3.11（继承自 base）、faster-whisper（CTranslate2）、NeMo（Parakeet-TDT）、FunASR（paraformer-zh）。

**Spec:** `docs/superpowers/specs/2026-10-04-transcribe-base-images-design.md`

## Global Constraints

- 两个 base（逐字，来自 spec）：`aiflowbase:0.4`（V100/sm_70，pytorch 2.4.1/CUDA 12.1）、`gpu50-baseimage:0.2`（RTX50/sm_120，pytorch 2.11.0/CUDA 12.8）。二者绝不 cross-compat，`gpu50-baseimage` 不需要兼容 sm_70。
- 三个镜像名：`whisper-transcribe-image`、`parakeet-transcribe-image`、`funasr-transcribe-image`。
- tag 约定：`<image>:<base>-<version>`，即 `v100-$VER` / `rtx50-$VER`；两个 base 的 tag 必须区分，防同名覆盖。
- 权重运行时 volume 挂载到 `/app/models/<模型名>`，**不 bake 进镜像**。
- 转写业务逻辑不进基础镜像：`CMD ["tail", "-f", "/dev/null"]`，继承 base 的 `/entrypoint.sh`（切 aigc 用户）。
- pip 源统一用阿里云镜像 `https://mirrors.aliyun.com/pypi/simple/`。
- 模型：faster-whisper 权重 `Systran/faster-whisper-large-v3`；parakeet 为 `nvidia/parakeet-tdt-0.6b-v3`；funasr 为 paraformer-zh。
- build 与 GPU 冒烟必须在带 NVIDIA GPU、装了 docker 的机器上执行：V100 机器验证 `aiflowbase:0.4`，RTX 50 机器验证 `gpu50-baseimage:0.2`。无 GPU 时只做 `docker build` 的语法/镜像层验证，`--gpus all` 冒烟推迟到有 GPU 的机器。
- 所有 commit message 英文，末尾带 `Co-Authored-By: Claude Code <noreply@anthropic.com>`（从下文的 heredoc 模板复制）。
- 每个镜像目录 9 个交付物：`Dockerfile`、`version.txt`、`build-<n>-v100-image.sh`、`build-<n>-rtx50-image.sh`、`start-<n>-v100-image.sh`、`start-<n>-rtx50-image.sh`、`stop-<n>-image.sh`、`docker-compose.yml`、`build_assets/requirements.txt`。

---

### Task 1: whisper 镜像（faster-whisper）

风险最低，先做，同时验证 `[待验证]-2`（ctranslate2 对 CUDA 12.1/12.8 的覆盖）。

**Files:**
- Create: `voice-image/transcribe-image/whisper-transcribe-image/Dockerfile`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/version.txt`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/build-whisper-v100-image.sh`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/build-whisper-rtx50-image.sh`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/start-whisper-v100-image.sh`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/start-whisper-rtx50-image.sh`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/stop-whisper-image.sh`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/docker-compose.yml`
- Create: `voice-image/transcribe-image/whisper-transcribe-image/build_assets/requirements.txt`

**Interfaces:**
- Consumes: `aiflowbase:0.4`、`gpu50-baseimage:0.2`（均已 build 好；当前仓库 baseimage 的 build 产物为 `aiflowbase:0.4`，见 `baseimage/build-aiflowbase-image.sh`）。
- Produces: 镜像 `whisper-transcribe-image:v100-$VER` / `whisper-transcribe-image:rtx50-$VER`；以及一套后续 task 复用的文件模板（Dockerfile + 脚本 + compose）。

- [ ] **Step 1: 写 9 个文件**

`version.txt`（一行，无换行结尾无所谓）：
```
0.1
```

`Dockerfile`：
```dockerfile
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
```

`build_assets/requirements.txt`：
```
faster-whisper
```

`build-whisper-v100-image.sh`：
```bash
#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t whisper-transcribe-image:v100-$VER \
    --build-arg BASE_IMAGE=aiflowbase:0.4 -f Dockerfile .
```

`build-whisper-rtx50-image.sh`：
```bash
#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t whisper-transcribe-image:rtx50-$VER \
    --build-arg BASE_IMAGE=gpu50-baseimage:0.2 -f Dockerfile .
```

`start-whisper-v100-image.sh`：
```bash
#!/usr/bin/env bash
set -e
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="v100-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d
```

`start-whisper-rtx50-image.sh`：
```bash
#!/usr/bin/env bash
set -e
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="rtx50-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d
```

`stop-whisper-image.sh`：
```bash
#!/usr/bin/env bash
set -e
docker compose -f docker-compose.yml down
```

`docker-compose.yml`（`device_ids` 与模型 volume 的宿主机路径按机器替换）：
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
              device_ids: ['2']          # 按机器 GPU 编号改
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

- [ ] **Step 2: 给脚本加执行权限**

Run: `chmod +x voice-image/transcribe-image/whisper-transcribe-image/*.sh`
Expected: 5 个 `.sh` 均 `-rwxr-xr-x`。

- [ ] **Step 3: build v100 镜像（V100 机器）**

Run: `bash voice-image/transcribe-image/whisper-transcribe-image/build-whisper-v100-image.sh`
Expected: 结束输出 `Successfully tagged whisper-transcribe-image:v100-0.1`。若 `docker buildx` 报 `Base image not found`，先确认 `docker images | grep aiflowbase` 有 `aiflowbase:0.4`。

- [ ] **Step 4: 冒烟验证 v100（import + GPU 可见）**

Run:
```bash
docker run --rm whisper-transcribe-image:v100-0.1 python3 -c "import faster_whisper; print(faster_whisper.__version__)"
docker run --gpus all --rm whisper-transcribe-image:v100-0.1 nvidia-smi
```
Expected: 第一条打印 faster-whisper 版本号；第二条 `nvidia-smi` 列出 V100 且驱动/CUDA 无报错。若 `nvidia-smi` 报 CUDA driver 不匹配，记录报错 —— 这是 `[待验证]-2` 的结论依据。

- [ ] **Step 5: 记录 ctranslate2 版本（`[待验证]-2`）**

Run: `docker run --rm whisper-transcribe-image:v100-0.1 pip show ctranslate2 | head -2`
Expected: 记录实际装的 ctranslate2 版本，并记下该版本在 CUDA 12.1 上是否可用（Step 4 的 GPU 冒烟结果）。rtx50 侧见 Step 7。

- [ ] **Step 6: build rtx50 镜像（RTX 50 机器）**

Run: `bash voice-image/transcribe-image/whisper-transcribe-image/build-whisper-rtx50-image.sh`
Expected: `Successfully tagged whisper-transcribe-image:rtx50-0.1`（先确认 `gpu50-baseimage:0.2` 存在）。

- [ ] **Step 7: 冒烟验证 rtx50 + 记录 ctranslate2**

Run:
```bash
docker run --gpus all --rm whisper-transcribe-image:rtx50-0.1 nvidia-smi
docker run --rm whisper-transcribe-image:rtx50-0.1 pip show ctranslate2 | head -2
```
Expected: `nvidia-smi` 列出 RTX 50；记录 ctranslate2 版本。若与 v100 侧同版本且两侧 GPU 冒烟都过，则 `[待验证]-2` 结论为「单版本通用」，无需分叉；否则在 requirements.txt 里按 CUDA 指定 ctranslate2 的 `cu11/cu12` 版本标记，并在 spec 待验证项里回填结论。

- [ ] **Step 8: commit**

```bash
cd /home/aigc/work/aiservice/aivoice_service/aiflow-gpu-images
git add voice-image/transcribe-image/whisper-transcribe-image
git commit -m "$(cat <<'EOF'
feat: add whisper transcribe base image (faster-whisper)

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: funasr 镜像（paraformer-zh）

中等风险，验证 `[待验证]-3`（funasr/torchaudio 在两个 torch 版本上的兼容）。

**Files:**
- Create: `voice-image/transcribe-image/funasr-transcribe-image/Dockerfile`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/version.txt`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/build-funasr-v100-image.sh`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/build-funasr-rtx50-image.sh`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/start-funasr-v100-image.sh`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/start-funasr-rtx50-image.sh`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/stop-funasr-image.sh`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/docker-compose.yml`
- Create: `voice-image/transcribe-image/funasr-transcribe-image/build_assets/requirements.txt`

**Interfaces:**
- Consumes: 与 Task 1 完全相同的模板（Dockerfile / 脚本 / compose 结构），仅名称替换为 funasr；`aiflowbase:0.4`、`gpu50-baseimage:0.2`。
- Produces: 镜像 `funasr-transcribe-image:v100-$VER` / `funasr-transcribe-image:rtx50-$VER`。

- [ ] **Step 1: 写 9 个文件（内容同 Task 1 模板，名称/镜像名/模型名替换）**

`version.txt`：
```
0.1
```

`Dockerfile`（与 Task 1 仅 `ARG BASE_IMAGE` 后的 `FROM` 一致，其余相同）：
```dockerfile
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
```

`build_assets/requirements.txt`：
```
funasr
```

`build-funasr-v100-image.sh`：
```bash
#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t funasr-transcribe-image:v100-$VER \
    --build-arg BASE_IMAGE=aiflowbase:0.4 -f Dockerfile .
```

`build-funasr-rtx50-image.sh`：
```bash
#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t funasr-transcribe-image:rtx50-$VER \
    --build-arg BASE_IMAGE=gpu50-baseimage:0.2 -f Dockerfile .
```

`start-funasr-v100-image.sh`：
```bash
#!/usr/bin/env bash
set -e
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="v100-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d
```

`start-funasr-rtx50-image.sh`：
```bash
#!/usr/bin/env bash
set -e
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="rtx50-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d
```

`stop-funasr-image.sh`：
```bash
#!/usr/bin/env bash
set -e
docker compose -f docker-compose.yml down
```

`docker-compose.yml`：
```yaml
services:
  funasr-transcribe:
    image: funasr-transcribe-image:${IMG_TAG:-v100-0.1}   # 值由 start-funasr-{v100,rtx50}-image.sh 传入
    hostname: funasr-transcribe
    container_name: funasr-transcribe
    restart: unless-stopped
    network_mode: host
    dns: [8.8.8.8, 1.1.1.1, 192.168.3.1]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['2']          # 按机器 GPU 编号改
              capabilities: [gpu]
    environment:
      - AIGC_UID=${AIGC_UID:-1001}
      - AIGC_GID=${AIGC_GID:-1001}
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - NVIDIA_REQUIRE_CUDA=cuda>=12.0
      - TZ=Asia/Shanghai
    volumes:
      - /path/to/paraformer-zh:/app/models/paraformer-zh
      - /home/aigc/data/aioutput/logs:/app/log
    extra_hosts:
      - host.docker.internal:host-gateway
```

- [ ] **Step 2: 加执行权限**

Run: `chmod +x voice-image/transcribe-image/funasr-transcribe-image/*.sh`

- [ ] **Step 3: build v100 + 冒烟**

Run:
```bash
bash voice-image/transcribe-image/funasr-transcribe-image/build-funasr-v100-image.sh
docker run --rm funasr-transcribe-image:v100-0.1 python3 -c "import funasr; print(funasr.__version__)"
docker run --gpus all --rm funasr-transcribe-image:v100-0.1 nvidia-smi
```
Expected: `Successfully tagged funasr-transcribe-image:v100-0.1`；打印 funasr 版本；`nvidia-smi` 正常。若 pip 装 funasr 时因 torch 版本报依赖冲突（如 torch/torchaudio du 要求不满足），记录报错 —— 这是 `[待验证]-3` 的结论依据。

- [ ] **Step 4: build rtx50 + 冒烟**

Run:
```bash
bash voice-image/transcribe-image/funasr-transcribe-image/build-funasr-rtx50-image.sh
docker run --gpus all --rm funasr-transcribe-image:rtx50-0.1 nvidia-smi
docker run --rm funasr-transcribe-image:rtx50-0.1 python3 -c "import funasr; print(funasr.__version__)"
```
Expected: 同 Step 3。若两侧同版本均装成功，`[待验证]-3` 结论为「单版本通用」。

- [ ] **Step 5: commit**

```bash
cd /home/aigc/work/aiservice/aivoice_service/aiflow-gpu-images
git add voice-image/transcribe-image/funasr-transcribe-image
git commit -m "$(cat <<'EOF'
feat: add funasr transcribe base image (paraformer-zh)

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: parakeet 镜像（Parakeet-TDT-0.6B-v3，NeMo）

三个里依赖最重、torch 约束最紧，验证 `[待验证]-1`（NeMo 在 pytorch 2.4.1 与 2.11.0 的可用版本组合）。此 task 有前置探测步骤，requirements 可能按 base 分叉。

**Files:**
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/Dockerfile`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/version.txt`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/build-parakeet-v100-image.sh`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/build-parakeet-rtx50-image.sh`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/start-parakeet-v100-image.sh`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/start-parakeet-rtx50-image.sh`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/stop-parakeet-image.sh`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/docker-compose.yml`
- Create: `voice-image/transcribe-image/parakeet-transcribe-image/build_assets/requirements.txt`
- Create（可能）: `voice-image/transcribe-image/parakeet-transcribe-image/build_assets/constraints.txt`（仅当需按 base 分叉依赖时）

**Interfaces:**
- Consumes: 与 Task 1/2 相同的模板；`aiflowbase:0.4`、`gpu50-baseimage:0.2`。
- Produces: 镜像 `parakeet-transcribe-image:v100-$VER` / `parakeet-transcribe-image:rtx50-$VER`。

- [ ] **Step 1: 探测 NeMo 可用版本（`[待验证]-1`）**

在 V100 机器做容器内试装，确认 Parakeet-TDT-0.6B-v3 的加载框架包名与版本：
```bash
docker run --rm aiflowbase:0.4 bash -c \
  "python3 -m pip install 'nemo_toolkit[asr]' -i https://mirrors.aliyun.com/pypi/simple/ 2>&1 | tail -20"
```
Expected/分支：
- 装成功 → `pip show nemo_toolkit` 记版本，并 `python3 -c "from nemo.collections.asr.models import ASRModel; print('ok')"` 验证 import。
- 装失败且报错指向 torch 版本不兼容 → 尝试新包名：`pip install 'open-nemo[asr]'`，同样验证 import。
- 记录：在 torch 2.4.1 下最终能用的「包名 + 版本」。
然后对 torch 2.11.0 在 RTX 50 机器重复同一探测（用 `gpu50-baseimage:0.2`）。

- [ ] **Step 2: 定 requirements（据 Step 1 结论）**

分支 A（两侧同一包名+版本通用）：`build_assets/requirements.txt` 写该包，如 `nemo_toolkit[asr]==<版本>`（用 Step 1 实测版本号替换 `<版本>`）。
分支 B（两侧包名或版本不同）：Dockerfile 按 `BASE_IMAGE` 条件选 requirements，新增 `build_assets/constraints.txt`，`requirements.txt` 写公共包 + `constraints.txt` 写分叉项；并在 `Dockerfile` 的 pip 步骤里按 base 加 `-c` 分支。具体以 Step 1 的实测为准，两个方向都在 spec `[待验证]-1` 回填结论。

- [ ] **Step 3: 写 9 个文件（模板同前，requirements 用 Step 2 结果）**

`version.txt`：
```
0.1
```

`Dockerfile`（若分支 B，则把 pip 步骤替换为按 base 的条件安装；分支 A 用以下纯 `requirements.txt` 版）：
```dockerfile
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
```

`build_assets/requirements.txt`（分支 A；`<版本>` 用 Step 1 实测值）：
```
nemo_toolkit[asr]==<版本>
```

`build-parakeet-v100-image.sh`：
```bash
#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t parakeet-transcribe-image:v100-$VER \
    --build-arg BASE_IMAGE=aiflowbase:0.4 -f Dockerfile .
```

`build-parakeet-rtx50-image.sh`：
```bash
#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t parakeet-transcribe-image:rtx50-$VER \
    --build-arg BASE_IMAGE=gpu50-baseimage:0.2 -f Dockerfile .
```

`start-parakeet-v100-image.sh`：
```bash
#!/usr/bin/env bash
set -e
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="v100-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d
```

`start-parakeet-rtx50-image.sh`：
```bash
#!/usr/bin/env bash
set -e
export AIGC_UID=${AIGC_UID:-$(id -u aigc 2>/dev/null || echo 1001)}
export AIGC_GID=${AIGC_GID:-$(id -g aigc 2>/dev/null || echo 1001)}
export IMG_TAG="rtx50-$(cat "$(dirname "$0")/version.txt")"
docker compose -f docker-compose.yml up -d
```

`stop-parakeet-image.sh`：
```bash
#!/usr/bin/env bash
set -e
docker compose -f docker-compose.yml down
```

`docker-compose.yml`：
```yaml
services:
  parakeet-transcribe:
    image: parakeet-transcribe-image:${IMG_TAG:-v100-0.1}   # 值由 start-parakeet-{v100,rtx50}-image.sh 传入
    hostname: parakeet-transcribe
    container_name: parakeet-transcribe
    restart: unless-stopped
    network_mode: host
    dns: [8.8.8.8, 1.1.1.1, 192.168.3.1]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['2']          # 按机器 GPU 编号改
              capabilities: [gpu]
    environment:
      - AIGC_UID=${AIGC_UID:-1001}
      - AIGC_GID=${AIGC_GID:-1001}
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - NVIDIA_REQUIRE_CUDA=cuda>=12.0
      - TZ=Asia/Shanghai
    volumes:
      - /path/to/parakeet-tdt-0.6b-v3:/app/models/parakeet-tdt-0.6b-v3
      - /home/aigc/data/aioutput/logs:/app/log
    extra_hosts:
      - host.docker.internal:host-gateway
```

- [ ] **Step 4: 加执行权限**

Run: `chmod +x voice-image/transcribe-image/parakeet-transcribe-image/*.sh`

- [ ] **Step 5: build v100 + 冒烟（import ASR 入口）**

Run:
```bash
bash voice-image/transcribe-image/parakeet-transcribe-image/build-parakeet-v100-image.sh
docker run --rm parakeet-transcribe-image:v100-0.1 python3 -c "from nemo.collections.asr.models import ASRModel; print('nemo asr ok')"
docker run --gpus all --rm parakeet-transcribe-image:v100-0.1 nvidia-smi
```
Expected: tag 成功；打印 `nemo asr ok`；`nvidia-smi` 正常。

- [ ] **Step 6: build rtx50 + 冒烟**

Run:
```bash
bash voice-image/transcribe-image/parakeet-transcribe-image/build-parakeet-rtx50-image.sh
docker run --gpus all --rm parakeet-transcribe-image:rtx50-0.1 nvidia-smi
docker run --rm parakeet-transcribe-image:rtx50-0.1 python3 -c "from nemo.collections.asr.models import ASRModel; print('nemo asr ok')"
```
Expected: 同 Step 5。

- [ ] **Step 7: （可选，需已下载权重）模型加载冒烟**

Run（挂载权重后）:
```bash
docker run --gpus all --rm -v /path/to/parakeet-tdt-0.6b-v3:/app/models/parakeet-tdt-0.6b-v3 \
    parakeet-transcribe-image:v100-0.1 python3 -c \
    "from nemo.collections.asr.models import ASRModel; ASRModel.from_pretrained('nvidia/parakeet-tdt-0.6b-v3'); print('model loaded')"
```
Expected: 打印 `model loaded`。若报 HF 网络不可达，改为本地路径加载并记录。

- [ ] **Step 8: commit**

```bash
cd /home/aigc/work/aiservice/aivoice_service/aiflow-gpu-images
git add voice-image/transcribe-image/parakeet-transcribe-image
git commit -m "$(cat <<'EOF'
feat: add parakeet transcribe base image (parakeet-tdt-0.6b-v3)

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### 收尾：回填 spec 的三个 `[待验证]` 项

三个 task 跑完后，把实测结论写回 `docs/superpowers/specs/2026-10-04-transcribe-base-images-design.md` 第 9 节：

- [ ] **Step 1: 更新第 9 节**，把每个 `[待验证]` 后附上实测结论（版本号、是否需分叉、分叉方案）。
- [ ] **Step 2: commit**

```bash
cd /home/aigc/work/aiservice/aivoice_service/aiflow-gpu-images
git add docs/superpowers/specs/2026-10-04-transcribe-base-images-design.md
git commit -m "$(cat <<'EOF'
docs: record transcribe dependency verification results

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```