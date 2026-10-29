# SEIF: Self-Evolving Reinforcement Learning for Instruction Following

[Paper](https://arxiv.org/abs/2605.07465) · [PDF](SEIF.pdf) · [Project](https://Rainier-rq1.github.io/SEIF/) · [User Guide](SEIF_User_Guide.pdf) · [License](LICENSE)

SEIF alternates GRPO training of an **Instructor**, which generates challenging multi-constraint instructions, and a **Follower**, which learns to satisfy them. A **Filter** rejects invalid instructions, and a **Judger** scores constraint satisfaction. Experiments use EasyR1, a veRL-based framework exposed here through the `verl` package.

<p align="center"><img src="assets/method.png" width="750" alt="SEIF training framework"></p>

## Method

Each round:

1. Train the Instructor against the current Follower.
2. Use the updated Instructor to generate Follower training data.
3. Train the Follower on the generated instructions.
4. Refresh the evaluator roles for the next round.

Both trainable roles start from the same base model and continue from their respective previous checkpoints. The Filter and Judger use the **pre-update Follower** and remain frozen throughout the round.

For constraint satisfaction rate `A` and filter decision `Q` (`1` = valid):

```text
Instructor reward = Q × (1 − A)
Follower reward   = A
```

The Instructor seeks valid instructions the Follower cannot yet satisfy; the Follower maximizes satisfaction (paper §2, equations 1–2).

## Setup

```bash
git clone https://github.com/Rainier-rq1/SEIF.git
cd SEIF
```

Use the [Dockerfile](Dockerfile) for the dependency environment: PyTorch `2.6.0`, vLLM `0.8.4`, and FlashAttention `2.7.4.post1`.

```bash
docker build -t seif:local .
docker run --gpus all --ipc=host --rm -it \
  -v "$PWD:/workspace/SEIF" -w /workspace/SEIF seif:local bash
```

Inside the container:

```bash
python -m pip install requests openai absl-py langdetect immutabledict nltk
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
```

`requirements.txt` is missing, so use this environment and `PYTHONPATH` rather than `pip install -e .`.

Run commands from the repository root. Replace model-path placeholders, set `trainer.save_checkpoint_path` in both configs, and assign separate GPUs to concurrent services and training. Export distributed checkpoints to Hugging Face format before serving; see `scripts/model_merger.py`.

## Training

### Role switching

Switch both files together, keeping only one role active:

- `examples/reward_function/instruction_reward.py`: Follower block at the top; Instructor block below.
- `verl/utils/dataset.py`: Instructor `RLHFDataset` first; Follower block below.

The Instructor is active by default. Restore the commented Follower blocks, including imports and helpers, before Follower training. Changing the YAML alone does not switch roles.

### 1. Train the Instructor

Set the evaluator scripts' `--model` to the base model for round 1, or the previous Follower thereafter. Start each service in a separate terminal:

| Command | Port | Served model |
| --- | --- | --- |
| `bash vllm_answer.sh` | `55222` | `if-answer` |
| `bash vllm_filter.sh` | `55333` | `if-filter` |
| `bash vllm_judge.sh` | `55111` | `if-judge` |

In the training terminal, set endpoints and launch training:

```bash
export ANSWER_VLLM_BASE_URL="http://localhost:55222/v1"
export FILTER_VLLM_BASE_URL="http://localhost:55333/v1"
export JUDGE_VLLM_BASE_URL="http://localhost:55111/v1"
bash examples/qwen.sh
```

Set `MODEL_PATH` in `examples/qwen.sh` to the base model for round 1, or the previous Instructor thereafter. Use the actual hostname for remote services; served-model names must match the clients.

### 2. Generate Follower data

Stop evaluator services before reusing their GPUs or port `55111`. Set `--model` in the generator server script to the updated Instructor, then run it in a separate terminal:

```bash
bash data/Self-IF-Self-QWEN-7B/vllm_chuti.sh
```

Prepare seed JSONL rows such as `{"prompt": "Explain photosynthesis."}`, then generate instructions:

```bash
export VLLM_BASE_URL="http://localhost:55111/v1"
export VLLM_MODEL="if-verifer"
python data/Self-IF-Self-QWEN-7B/chuti.py \
  --input_jsonl /path/to/seeds.jsonl \
  --output_jsonl /path/to/q_T1.jsonl \
  --num_workers 8
```

**The current Qwen-7B generator has invalid UTF-8 bytes and must be repaired before running.** Alternatively, use released `q_T*.parquet` files.

The generator appends JSONL, not Parquet. Use a fresh output path and convert before training:

```bash
python -c 'import pandas as pd; pd.read_json("/path/to/q_T1.jsonl", lines=True).to_parquet("/path/to/q_T1.parquet", index=False)'
```

Follower data requires `prompt`, `instruction_id_list`, `kwargs`, and `constraint`. Keep the three constraint lists aligned and non-empty; the loader maps `constraint` to reward metadata `constraints`.

### 3. Train the Follower

Stop the generator service and activate the Follower blocks. Configure:

- `examples/config1.yaml`: round-specific `data.train_files`, integer `trainer.total_epochs` (`3` for round 1, `1` later), and `trainer.save_checkpoint_path`.
- `examples/qwen1.sh`: `MODEL_PATH` = base model for round 1, previous Follower later.
- `vllm_verifer.sh`: `--model` = the same pre-update Follower checkpoint.
- Follower reward: replace `YOUR_VLLM_HOST` in `openai_api_base` with the verifier host; the served name is `if-verifer`.

Start the verifier and training in separate terminals:

| Command | Purpose |
| --- | --- |
| `bash vllm_verifer.sh` | Frozen verifier on port `55111` |
| `bash examples/qwen1.sh` | Follower training |

Preserve the required `<think>...</think><answer>...</answer>` response format. The implementation uses registry checkers for hard constraints and model verification for semantic constraints.

## Experiment Configuration

| Setting | Instructor | Follower |
| --- | --- | --- |
| Config | `examples/config.yaml` | `examples/config1.yaml` |
| Training data | `data/seed.parquet` | `q_T*.parquet` |
| Steps, rounds 1/2/3 | `13/13/13` | `39/13/13` |
| Rollouts per prompt | `5` | `5` |

Paper Appendix B reports **8 H200 training GPUs + 4 H200 serving GPUs**. The training-schedule study favors `3-1-1` Follower epochs. Adjust batch sizes and GPU allocation for your hardware; authenticate with `wandb login` if retaining the default logger.

## Citation

```bibtex
@misc{ren2026seif,
  title={SEIF: Self-Evolving Reinforcement Learning for Instruction Following},
  author={Qingyu Ren and Qianyu He and Jiajie Zhu and Xingzhou Chen and Jingwen Chang and Zeye Sun and Han Xia and Fei Yu and Jiaqing Liang and Yanghua Xiao},
  year={2026},
  eprint={2605.07465},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2605.07465}
}
```
