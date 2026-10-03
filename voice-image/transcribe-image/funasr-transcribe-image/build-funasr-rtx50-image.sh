#!/usr/bin/env bash
set -e
VER=$(cat "$(dirname "$0")/version.txt")
docker build -t funasr-transcribe-image:rtx50-$VER \
    --build-arg BASE_IMAGE=gpu50-baseimage:0.2 -f Dockerfile .