export CUDA_VISIBLE_DEVICES=0,1,2,3

python -m vllm.entrypoints.openai.api_server \
    --port 55111 \
    --served-model-name if-verifer \
    --model path to latest follower checkpoint \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.85 \
    --dtype auto \
    --max-model-len 32000 \


    
