echo "set hyperframes origin host directory permission..."

HOST_USER="${HOST_USER:-aigc}"
HOST_UID="${HOST_UID:-$(id -u "${HOST_USER}" 2>/dev/null || echo 1001)}"
HOST_GID="${HOST_GID:-$(id -g "${HOST_USER}" 2>/dev/null || echo 1001)}"
echo "use HOST_UID=${HOST_UID} HOST_GID=${HOST_GID}"

# 确保目录存在
mkdir -p /home/aigc/data/aioutput/hyperframes-origin-logs
# 设置目录权限，确保可以写入
chmod -R 755 /home/aigc/data/aioutput/hyperframes-origin-logs/

mkdir -p /home/aigc/data/aioutput/videos
chmod -R 755 /home/aigc/data/aioutput/videos/

echo "permission set completed!"
echo "directory permission information:"
ls -la /home/aigc/data/aioutput/hyperframes-origin-logs/