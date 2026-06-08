注意：build前需要单独下载 flash_attn-2.8.3+cu128torch2.9-cp314-cp314t-linux_aarch64.whl 文件放在 build_assets 目录。

## 運行時 UID/GID 對齊（可選）

若希望容器內進程與宿主机上的 `aigc` 用戶 UID/GID 一致，在運行容器時傳入環境變數：

```bash
docker run -e AIGC_UID=$(id -u aigc) -e AIGC_GID=$(id -g aigc) -it aiflowbase:0.3
```

未傳入時預設為 1001:1001。