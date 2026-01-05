#!/bin/sh

echo "Starting mt_worker"
export CUDA_VISIBLE_DEVICES=${GPU_INDEX:-0}
echo "Using GPU: ${CUDA_VISIBLE_DEVICES}"
python3 -m vllm.entrypoints.openai.api_server --model /app/models/mt_models \
  --host 0.0.0.0 \
  --port ${APP_PORT:-5400} \
  --tensor-parallel-size ${TENSOR_PARALLEL_SIZE:-1} \
  --dtype bfloat16 \
  --max-model-len 1024 \
  --gpu_memory_utilization 0.5 \
  --served-model-name mt-model \
  --trust-remote-code \
  --hf-overrides '{"architectures": ["LlamaForCausalLM"]}' \
  2>&1 | tee /app/log/mt_server.log
