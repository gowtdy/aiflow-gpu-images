docker build -t aiflowbase:0.4.1 -f Dockerfile .

# Run with host aigc UID/GID: docker run -e AIGC_UID=$(id -u aigc) -e AIGC_GID=$(id -g aigc) -it aiflowbase:0.3 ...
#docker build -t 100.95.222.4:2000/aiflowbase:0.1 -f Dockerfile .
#docker push 100.95.222.4:2000/aiflowbase:0.1