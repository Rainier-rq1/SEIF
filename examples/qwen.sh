


MODEL_PATH=path to latest instructor checkpoint
python3 -m verl.trainer.main \
    config=examples/config.yaml \
    worker.actor.model.model_path=${MODEL_PATH} \
    trainer.n_gpus_per_node=8 \


    

    
