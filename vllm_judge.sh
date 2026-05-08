export CUDA_VISIBLE_DEVICES=0,1

python -m vllm.entrypoints.openai.api_server \
    --port 55111 \
    --served-model-name if-judge\
    --model path to latest follower checkpoint \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.85 \
    --dtype auto \
    --max-model-len 32000 \


    
