#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t funasr-transcribe-image:v100-$VER \
    --build-arg BASE_IMAGE=aiflowbase:0.4 -f Dockerfile .