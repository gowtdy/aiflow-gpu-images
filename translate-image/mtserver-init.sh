echo "Initializing mtserver"

sudo mkdir -p /home/aigc/data/aioutput/mtserver-logs/mtserver
sudo chown -R aigc:aigc /home/aigc/data/aioutput/mtserver-logs/mtserver
sudo chmod -R 755 /home/aigc/data/aioutput/mtserver-logs/mtserver

echo "mtserver initialized"
ls -la /home/aigc/data/aioutput/mtserver-logs/