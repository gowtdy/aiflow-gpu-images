# Build hyperframes-local image (FROM gpu50-baseimage:0.1). Run 時由 base entrypoint 依 AIGC_UID/AIGC_GID 建立 aigc，B 機可傳 -e AIGC_UID=$(id -u aigc) -e AIGC_GID=$(id -g aigc)，未傳則預設 1001。
docker build --progress=plain -t hyperframes-local-image:0.1 -f Dockerfile .
