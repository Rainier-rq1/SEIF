import importlib.util
import os
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import partial
from typing import Callable, Dict, List, Optional, Tuple, TypedDict

import torch
from transformers import PreTrainedTokenizer

from ...protocol import DataProto
from .config import RewardConfig


class RewardScore(TypedDict):
    overall: float
    format: Optional[float]
    accuracy: Optional[float]


SequentialRewardFunction = Callable[[str, str], RewardScore]

BatchRewardFunction = Callable[[List[str], List[str]], List[RewardScore]]


class FunctionRewardManager(ABC):
    """Reward manager for rule-based reward."""

    def __init__(self, config: RewardConfig, tokenizer: PreTrainedTokenizer):
        if config.reward_function is None:
            raise ValueError("Reward function is not provided.")

        if not os.path.exists(config.reward_function):
            raise FileNotFoundError(f"Reward function file {config.reward_function} not found.")

        spec = importlib.util.spec_from_file_location("custom_reward_fn", config.reward_function)
        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules["custom_reward_fn"] = module
            spec.loader.exec_module(module)
        except Exception as e:
            raise RuntimeError(f"Failed to load reward function: {e}")

        if not hasattr(module, config.reward_function_name):
            raise AttributeError(f"Module {module} does not have function {config.reward_function_name}.")

        reward_fn = getattr(module, config.reward_function_name)
        print(f"Using reward function `{config.reward_function_name}` from `{config.reward_function}`.")
        self.reward_fn = partial(reward_fn, **config.reward_function_kwargs)
        self.config = config
        self.tokenizer = tokenizer

    @abstractmethod
    def compute_reward(self, data: DataProto) -> Tuple[torch.Tensor, Dict[str, List[float]]]:
        """Compute reward for a batch of data."""
        ...


class SequentialFunctionRewardManager(FunctionRewardManager):
    reward_fn: SequentialRewardFunction

    def compute_reward(self, data: DataProto) -> Tuple[torch.Tensor, Dict[str, List[float]]]:
        reward_tensor = torch.zeros_like(data.batch["responses"], dtype=torch.float32)
        reward_metrics = defaultdict(list)
        response_ids = data.batch["responses"]
        response_length = data.batch["response_mask"].sum(dim=-1)
        ac_count=0
        c_count=0
        score_l=0
        for i in range(len(data)):
            valid_response_ids = response_ids[i][: response_length[i]]
            response_str = self.tokenizer.decode(
                valid_response_ids, skip_special_tokens=self.config.skip_special_tokens
            )
            ground_truth = data.non_tensor_batch["ground_truth"][i]
            
            # score = self.reward_fn(response_str, ground_truth)
            # reward_tensor[i, response_length[i] - 1] = score["overall"]
            if self.config.reward_function_name == "instruction_compute_score":
                score = self.reward_fn(response_str, ground_truth)
                score_c =0
                score_l = 0
                reward_metrics['overall'].append(score)
                reward_metrics['format'].append(score_c)
                reward_metrics['accuracy'].append(score_l)
            elif self.config.reward_function_name == "instruction_val_compute_score":
                all_right,a_len_c,len_c,score = self.reward_fn(response_str, ground_truth)
                ac_count+=a_len_c
                c_count+=len_c
                score_l +=all_right
                score_c =ac_count/c_count
                score_l = score_l/len(data)
                reward_metrics['overall'].append(score)
                reward_metrics['format'].append(score_c)
                reward_metrics['accuracy'].append(score_l)
            
            reward_tensor[i, response_length[i] - 1] = score
            
            

        return reward_tensor, reward_metrics


class BatchFunctionRewardManager(FunctionRewardManager):
    reward_fn: BatchRewardFunction

    def compute_reward(self, data: DataProto) -> Tuple[torch.Tensor, Dict[str, List[float]]]:
        response_str, ground_truth = [], []
        response_ids = data.batch["responses"]
        response_length = data.batch["response_mask"].sum(dim=-1)
        ac_count=0
        c_count=0
        score_l=0
        for i in range(len(data)):
            valid_response_ids = response_ids[i][: response_length[i]]
            response_str.append(
                self.tokenizer.decode(valid_response_ids, skip_special_tokens=self.config.skip_special_tokens)
            )
            ground_truth.append(data.non_tensor_batch["ground_truth"][i])


        reward_tensor = torch.zeros_like(data.batch["responses"], dtype=torch.float32)
        reward_metrics = defaultdict(list)

        if self.config.reward_function_name == "instruction_val_compute_score":
            for resp, gt in zip(response_str, ground_truth):
                all_right, a_len_c, len_c, score = self.reward_fn(resp, gt)
                ac_count+=a_len_c
                c_count+=len_c
                score_l +=all_right
                score_c =ac_count/c_count
                score_l = score_l/len(data)
                reward_metrics['overall'].append(score)
                reward_metrics['format'].append(score_c)
                reward_metrics['accuracy'].append(score_l)
        elif self.config.reward_function_name == "instruction_compute_score":
            scores = self.reward_fn(response_str, ground_truth)
            for i, score in enumerate(scores):
                reward_tensor[i, response_length[i] - 1] = score
                score_c =0
                score_l = 0
                reward_metrics['overall'].append(score)
                reward_metrics['format'].append(score_c)
                reward_metrics['accuracy'].append(score_l)

        return reward_tensor, reward_metrics