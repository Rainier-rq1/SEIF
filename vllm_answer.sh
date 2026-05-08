export CUDA_VISIBLE_DEVICES=2

python -m vllm.entrypoints.openai.api_server \
    --port 55222 \
    --served-model-name if-answer \
    --model path to latest follower checkpoint \
    --tensor-parallel-size 1\
    --gpu-memory-utilization 0.85 \
    --dtype auto \
    # --max-model-len 32000 \
