# SEIF: Self-Evolving Reinforcement Learning for Instruction Following

SEIF is an iterative self-training framework for instruction following built on top of [verl](https://github.com/volcengine/verl). Two roles co-evolve:

- **Instructor** — generates diverse, challenging multi-constraint instructions.
- **Follower** — learns to satisfy those instructions.

Each round, the Instructor is optimized against the *latest* Follower as evaluator (pushing it to produce instructions the Follower can't yet handle), then the Follower is trained on the new instructions. This closed loop lets instruction difficulty scale with model capability, unlike methods that rely on external supervision or static difficulty.

<p align="center"><img src="assets/comp.png" width="800"></p>
<p align="center"><img src="assets/method.png" width="750"></p>

## The self-evolving loop

For round `T` (T ≥ 1):

1. **Train Instructor `I_T`** on `data/seed.parquet` using GRPO. The evaluator is the base model for `T=1`, else the previous Follower `F_{T-1}`.
2. **Generate data** — serve `I_T` and run `chuti.py` to produce `q_T{T}.parquet` (multi-constraint instructions).
3. **Train Follower `F_T`** on `q_T{T}.parquet`. Initialized from the base model for `T=1`, else `F_{T-1}`.
4. `F_T` becomes the evaluator for round `T+1`.

| Turn | Instructor            | Follower            | Data           |
| ---- | --------------------- | ------------------- | -------------- |
| 1    | `I_1` from base       | `F_1` from base     | `q_T1.parquet` |
| 2    | `I_2` from `I_1`, eval `F_1` | `F_2` from `F_1` | `q_T2.parquet` |
| 3    | `I_3` from `I_2`, eval `F_2` | `F_3` from `F_2` | `q_T3.parquet` |

## Setup

- Install `verl`, `vllm`, `ray` and other deps (see `pyproject.toml` / `Dockerfile`).
- Prepare seed data at `data/seed.parquet` and a base model (e.g. `Qwen/Qwen2.5-7B-Instruct`).
- Allocate GPUs for both vLLM serving and training.

## Switching between Instructor and Follower

Both roles share the same reward and dataset files; exactly **one** role must be active at a time by commenting/uncommenting blocks:

- `examples/reward_function/instruction_reward.py` — Instructor reward at the top; Follower reward below (~lines 1–1040).
- `verl/utils/dataset.py` — Instructor `RLHFDataset` (~line 220); Follower `RLHFDataset` (~lines 375–483).

## Running a round

**1. Train the Instructor** — start the three evaluator servers, then launch training:

```bash
bash vllm_answer.sh     # answers, port 55222
bash vllm_filter.sh     # conflict filter, port 55333
bash vllm_judge.sh      # constraint judge, port 55111

# set MODEL_PATH / SAVE_PATH in examples/qwen.sh, then:
bash examples/qwen.sh   # → Instructor checkpoint I_T
```

For `T ≥ 2`, point the three server scripts' `MODEL_PATH` at `F_{T-1}` and set `qwen.sh`'s `MODEL_PATH` to `I_{T-1}`.

**2. Generate Follower data** — serve `I_T` and run the generator:

```bash
bash data/Self-IF-Self-QWEN-7B/vllm_chuti.sh
cd data/Self-IF-Self-QWEN-7B && python chuti.py   # → q_T{T}.parquet
```

**3. Train the Follower** — set `train_files` in `config1.yaml` and `MODEL_PATH`/`SAVE_PATH`/`DATA_PATH` in `qwen1.sh`, then:

```bash
bash vllm_verifer.sh    # verifier (base model for T=1, else F_{T-1})
bash examples/qwen1.sh  # → Follower checkpoint F_T
```

> Switch the active blocks in `instruction_reward.py` and `dataset.py` to match the role you're training (see above).

## Reward functions

Both live in `examples/reward_function/instruction_reward.py`; the active one depends on which block is uncommented.

- **Instructor** — parse constraints → `FILTER_VLLM` drops conflicting ones → `ANSWER_VLLM` answers → `JUDGE_VLLM` checks each. `score = followed / valid`.
- **Follower** — evaluate each constraint from the parquet (`instruction_id_list`, `kwargs`, `constraints`) via `instructions_registry` and `check_following()`. `score = followed / total`.

## Configuration

- `examples/config.yaml` — Instructor training (`train_files: data/seed.parquet`, GRPO, `n=5`).
- `examples/config1.yaml` — Follower training (`train_files: q_T{T}.parquet`; `total_epochs: 3` for Turn 1, else `1`).

## Layout

```text
vllm_*.sh                       # vLLM servers (answer/filter/judge/verifier)
examples/
  config.yaml / config1.yaml    # Instructor / Follower training configs
  qwen.sh    / qwen1.sh         # Instructor / Follower launchers
  reward_function/instruction_reward.py
verl/                           # RL framework (trainer, utils/dataset.py, ...)
data/
  seed.parquet                  # seed questions
  Self-IF-Self-QWEN-7B/         # per-model data + chuti.py generator (also 1.5B, LLAMA-8B, DISTILL-14B, R1-QWEN3)
```

See `SEIF_User_Guide.pdf` for the full walkthrough.
