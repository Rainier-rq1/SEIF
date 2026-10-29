# SEIF: Self-Evolving Reinforcement Learning for Instruction Following

[Paper](https://arxiv.org/abs/2605.07465) · [PDF](SEIF.pdf) · [Project](https://Rainier-rq1.github.io/SEIF/) · [User Guide](SEIF_User_Guide.pdf) · [License](LICENSE)

SEIF improves instruction following by alternately training an **Instructor** to generate challenging instructions and a **Follower** to satisfy them. A **Filter** checks instruction validity, and a **Judger** scores constraint satisfaction. Both trainable roles use GRPO with EasyR1, a veRL-based framework.

<p align="center"><img src="assets/method.png" width="750" alt="SEIF training framework"></p>

## Method

Each round follows three steps: **train Instructor → generate instructions → train Follower**.

Both roles start from the same base model and continue from their own previous checkpoints. The Filter and Judger use the pre-update Follower, stay frozen within the round, and refresh for the next round.

For satisfaction rate `A` and validity decision `Q` (`1` = valid):

```text
Instructor reward = Q × (1 − A)
Follower reward   = A
```

## Setup

```bash
git clone https://github.com/Rainier-rq1/SEIF.git
cd SEIF
docker build -t seif:local .
docker run --gpus all --ipc=host --rm -it \
  -v "$PWD:/workspace/SEIF" -w /workspace/SEIF seif:local bash
```

Inside the container:

```bash
python -m pip install requests openai absl-py langdetect immutabledict nltk
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
```

Set model paths, checkpoint output paths, and GPU assignments before training. Run commands from the repository root.

## Training

Switch the Instructor/Follower blocks in both files before each stage:

- `examples/reward_function/instruction_reward.py`
- `verl/utils/dataset.py`

Keep one role active at a time; the Instructor is active by default.

### 1. Train the Instructor

Use the base model as evaluator in round 1 and the previous Follower thereafter. Start the services in separate terminals:

| Command | Port |
| --- | --- |
| `bash vllm_answer.sh` | `55222` |
| `bash vllm_filter.sh` | `55333` |
| `bash vllm_judge.sh` | `55111` |

Set `MODEL_PATH` in `examples/qwen.sh` to the base model or previous Instructor, then launch:

```bash
export ANSWER_VLLM_BASE_URL="http://localhost:55222/v1"
export FILTER_VLLM_BASE_URL="http://localhost:55333/v1"
export JUDGE_VLLM_BASE_URL="http://localhost:55111/v1"
bash examples/qwen.sh
```

### 2. Prepare Follower data

Released round-specific data is in `data/Self-IF-Self-*/q_T*.parquet`.

For new instructions, serve the updated Instructor with `vllm_chuti.sh` and use the corresponding `chuti.py` generator. The Qwen-7B generator outputs JSONL; convert it to Parquet for training.

Follower data uses four columns: `prompt`, `instruction_id_list`, `kwargs`, and `constraint`.

### 3. Train the Follower

Activate the Follower blocks and configure:

- `examples/config1.yaml`: training data, checkpoint output path, and integer `total_epochs` (`3` for round 1, `1` later).
- `examples/qwen1.sh`: base model for round 1, previous Follower later.
- `vllm_verifer.sh` and Follower reward: matching model path and verifier endpoint (`if-verifer`, port `55111`).

Start `bash vllm_verifer.sh` in one terminal and `bash examples/qwen1.sh` in another. Stop the judge or generation service before reusing port `55111`.

## Configuration

| | Instructor | Follower |
| --- | --- | --- |
| Config | `examples/config.yaml` | `examples/config1.yaml` |
| Data | `data/seed.parquet` | `q_T*.parquet` |
| Steps, rounds 1/2/3 | `13/13/13` | `39/13/13` |

Paper experiments use 8 H200 GPUs for training and 4 for vLLM services, with 5 rollouts per prompt.

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
