export CUDA_VISIBLE_DEVICES=3

python -m vllm.entrypoints.openai.api_server \
    --port 55333 \
    --served-model-name if-filter \
    --model path to latest follower checkpoint \
    --tensor-parallel-size 1\
    --gpu-memory-utilization 0.85 \
    --dtype auto \
    # --max-model-len 32000 \
