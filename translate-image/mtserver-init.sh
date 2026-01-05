echo "Initializing mtserver"

mkdir -p /home/aigc/data/aioutput/mtserver-logs/mtserver
chown -R aigc:aigc /home/aigc/data/aioutput/mtserver-logs
chmod -R 755 /home/aigc/data/aioutput/mtserver-logs

echo "mtserver initialized"
ls -la /home/aigc/data/aioutput/mtserver-logs/