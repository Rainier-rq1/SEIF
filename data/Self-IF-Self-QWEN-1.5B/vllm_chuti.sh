export CUDA_VISIBLE_DEVICES=0,1

python -m vllm.entrypoints.openai.api_server \
    --port 55111 \
    --served-model-name if-verifer \
    --model path to latest Instructor model \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.99 \
    --dtype auto \
    --max-model-len 32000 \
