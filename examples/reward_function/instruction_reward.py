# # **************************Follower Training**************************
# import re
# from modules import instructions_registry
# from mathruler.grader import extract_boxed_content
# import requests
# import json
# import inspect
# from openai import OpenAI
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from datetime import datetime, timezone


# openai_api_key = "EMPTY"
# openai_api_base = "http://YOUR_VLLM_HOST:55111/v1"
# client = OpenAI(
#     api_key=openai_api_key,
#     base_url=openai_api_base,
# )

# def compute_score(expr: str, gt: list) -> float:
#     positions = []
#     idx = 0
#     while idx < len(expr):
#         if expr.startswith("boxed{", idx):
#             start = idx + len("boxed{")
#             stack = ["{"]
#             i = start
#             while i < len(expr) and stack:
#                 if expr[i] == "{":
#                     stack.append("{")
#                 elif expr[i] == "}":
#                     stack.pop()
#                 i += 1
#             if not stack:
#                 boxed_content = expr[start:i-1]
#                 positions.append(boxed_content)
#             idx = i
#         else:
#             idx += 1
#     if positions:
#         if(positions[-1]=="self-contradiction"):
#             positions[-1]="self_contradiction"  
#         if positions[-1].replace("\\", "") == gt[0].replace("\\", ""):
#             return 1.0
#         else:
#             return 0.0
#     else:
#         return 0.0

# def extract_score(text):
#     match = re.search(r'\[\[(\d+)\]\]', text)
#     try:
#         return int(match.group(1))
#     except:
#         return 0

# def call_build_description(obj, args):

#     method_signature = inspect.signature(obj.build_description)

#     valid_params = set(method_signature.parameters.keys())

#     filtered_args = {k: v for k, v in args.items() if k in valid_params}

#     return obj.build_description(**filtered_args)



# def _append_jsonl(path: str, record: dict) -> None:
#     with open(path, "a", encoding="utf-8") as f:
#         f.write(json.dumps(record, ensure_ascii=False) + "\n")


# def instruction_compute_score(answers, items, jsonl_path: str = "answer_score.jsonl", log_enabled: bool = True):
#     n_items = len(items)
#     all_scores = [[None] * len(item['instruction_id_list']) for item in items]

#     processed_items = set()
#     client_queries_global = []

#     for item_idx, (answer, item) in enumerate(zip(answers, items)):
#         pattern = re.compile(r"<think>.*?</think>\s*<answer>(.*?)</answer>", re.DOTALL)
#         answer_match = re.fullmatch(pattern, answer)
#         # answer_match = re.search(r"</think>\n(.*)", answer, re.DOTALL)

#         if not answer_match:
#             continue
#         resp_to_check = answer_match.group(1)
#         ids_to_check = item['instruction_id_list']
#         args_to_check = item['kwargs']
#         constraints = item['constraints']

#         for ids in ids_to_check:
#             if ids == 'light':
#                 res = compute_score(resp_to_check, constraints[0]) * 5
#                 all_scores[item_idx] = [float(res)]
#                 processed_items.add(item_idx)
#                 break
#             if ids == 'light_choice':
#                 boxed_answer = extract_boxed_content(resp_to_check)
#                 if boxed_answer == "None":
#                     matches = re.findall(r'boxed{(.*?)}', resp_to_check)
#                     if matches:
#                         boxed_answer = matches[-1]
#                 score = 5.0 if boxed_answer == constraints[0] else 0.0
#                 all_scores[item_idx] = [score]
#                 processed_items.add(item_idx)
#                 break
#         if item_idx in processed_items:
#             continue

#         for con_idx, (ids, con) in enumerate(zip(ids_to_check, constraints)):
#             if ids in [
#                 'soft_content:language', 'soft', 'soft_content:open_ended',
#                 'situation:suggestion', 'situation:role_play',
#                 'situation:story_generation', 'style:open_ended'
#             ]:
#                 few_shot_examples = """## Examples:

# ### Example 1:
# [Reply]
# Kathy and Sue are the two characters in this story.
# [Constraint]
# The response should include at least three characters from the story.
# [Analysis]
# The reply mentions only "Kathy" and "Sue", which is 2 characters. The constraint requires at least 3 characters.
# NOT SATISFIED [[0]]

# ### Example 2:
# [Reply]
# Kathy
# Sue
# John
# [Constraint]
# The response should include at least three characters from the story.
# [Analysis]
# The reply mentions "Kathy", "Sue", and "John", which is 3 characters. This satisfies the constraint.
# SATISFIED [[1]]

# ### Example 3:
# [Reply]
# The characters in this story are Kathy and Sue.
# Kathy is mentioned in multiple sentences.
# Sue appears in the conflict described.
# [Constraint]
# Each character's name must appear in a different paragraph.
# [Analysis]
# The reply has 3 paragraphs: 1) "The characters in this story are Kathy and Sue." 2) "Kathy is mentioned..." 3) "Sue appears..."
# Each paragraph contains a character name.
# SATISFIED [[1]]

# ### Example 4:
# [Reply]
# Kathy and Sue are friends. They talk every day.
# [Constraint]
# Each character's name must appear in a different paragraph.
# [Analysis]
# The reply has only 1 paragraph. Both character names appear in the same paragraph.
# NOT SATISFIED [[0]]

# ### Example 5:
# [Reply]
# The answer is five.
# [Constraint]
# The response must include the word 'count' exactly once.
# [Analysis]
# The reply does not contain the word "count".
# NOT SATISFIED [[0]]

# ### Example 6:
# [Reply]
# Let me count the items for you.
# [Constraint]
# The response must include the word 'count' exactly once.
# [Analysis]
# The reply contains "count" exactly once in "Let me count". No other occurrences of "count".
# SATISFIED [[1]]

# ### Example 7:
# [Reply]
# I will count the number of items. Please count them carefully.
# [Constraint]
# The response must include the word 'count' exactly once.
# [Analysis]
# The reply contains "count" twice: "I will count" and "Please count them". This is more than once.
# NOT SATISFIED [[0]]

# ### Example 8:
# [Reply]
# Kathy Sue John
# [Constraint]
# The response should not use any commas.
# [Analysis]
# The reply contains no commas, only spaces between the names.
# SATISFIED [[1]]

# ### Example 9:
# [Reply]
# Kathy, Sue, and John are the characters.
# [Constraint]
# The response should not use any commas.
# [Analysis]
# The reply contains commas: "Kathy, Sue, and John".
# NOT SATISFIED [[0]]

# """
#                 query = (
#                     "Please judge whether the given reply follows the constraint(s). "
#                     "Analyze each constraint one by one and determine if it is satisfied.\n"
#                     f"{few_shot_examples}"
#                     "Now judge the following:\n"
#                     "[Reply]\n"
#                     f"{resp_to_check}\n"
#                     "[Constraint]\n"
#                     f"{con}\n"
#                     "Output your analysis and then the final score in [[score]] format. "
#                     "If ALL constraints are satisfied output [[1]] otherwise output [[0]]."
#                 )
#                 # query =(
#                 #     "Please judge whether the given reply follows the constraint (e.g., length, style, format).\n"
#                 #     "[Reply]\n"
#                 #     f"{resp_to_check}\n"
#                 #     "[Constraint]\n"
#                 #     f"{con}\n"
#                 #     "You MUST output the score in the very beginning of your answer using the [[score]] format. "
#                 #     "If it follows the constraint output [[1]] otherwise output [[0]]."
#                 # )

#                 client_queries_global.append((item_idx, con_idx, query))

#     if client_queries_global:
#         with ThreadPoolExecutor(max_workers=500) as executor:
#             future_to_pos = {
#                 executor.submit(
#                     client.chat.completions.create,
#                     model="if-verifer",
#                     messages=[{"role": "user", "content": query}],
#                     max_tokens=8192
#                 ): (item_idx, con_idx)
#                 for (item_idx, con_idx, query) in client_queries_global
#             }
#             for future in as_completed(future_to_pos):
#                 item_idx, con_idx = future_to_pos[future]
#                 try:
#                     response = future.result()
#                     generated_text = response.choices[0].message.content
#                     answer_match11 = re.search(r"</think>\n(.*)", generated_text, re.DOTALL)
#                     if answer_match11:
#                         generated_text = answer_match11.group(1)
#                     score_match = re.search(r"\[\[(\d+)\]\]", generated_text)
#                     score_val = int(score_match.group(1)) if score_match else 0
#                     all_scores[item_idx][con_idx] = score_val
#                 except Exception:
#                     all_scores[item_idx][con_idx] = 0

#     for item_idx, (answer, item) in enumerate(zip(answers, items)):
#         if item_idx in processed_items:
#             continue
#         pattern = re.compile(r"<think>.*?</think>\s*<answer>(.*?)</answer>", re.DOTALL)
#         answer_match = re.fullmatch(pattern, answer)
#         #answer_match = re.search(r"</think>\n(.*)", answer, re.DOTALL)
#         if not answer_match:
#             continue
#         resp_to_check = answer_match.group(1)
#         ids_to_check = item['instruction_id_list']
#         args_to_check = item['kwargs']
#         constraints = item['constraints']

#         for con_idx, (ids, arg, con) in enumerate(zip(ids_to_check, args_to_check, constraints)):
#             if all_scores[item_idx][con_idx] is not None:
#                 continue
#             instruction_cls = instructions_registry.INSTRUCTION_DICT[ids]
#             instruction = instruction_cls(ids)
#             call_build_description(instruction, arg)
#             all_scores[item_idx][con_idx] = (
#                 1 if resp_to_check.strip() and instruction.check_following(resp_to_check) else 0
#             )

#     final_scores = []
#     for scores in all_scores:
#         valid_scores = [s for s in scores if s is not None]
#         if not valid_scores:
#             final_scores.append(0.0)
#         else:
#             final_scores.append(sum(valid_scores) / len(valid_scores))

#     if log_enabled and jsonl_path:
#         ts = datetime.now(timezone.utc).isoformat()
#         for idx, (answer, score) in enumerate(zip(answers, final_scores)):
#             _append_jsonl(
#                 jsonl_path,
#                 {
#                     "ts": ts,
#                     "idx": idx,
#                     "answer": answer,
#                     "score": float(score),
#                 },
#             )

#     return final_scores


# def instruction_val_compute_score(answer, item):
    
#     import requests
#     import json
    
#     answer_pattern = r'<answer>(.*?)</answer>'
#     answer_match = re.search(answer_pattern, answer, re.DOTALL)
#     #answer_match = re.search(r"</think>\n(.*)", answer, re.DOTALL)

#     if not answer_match:
#         # print("not answer_match")
#         return 0,0,len(item),0
    
#     ids_to_check = item['instruction_id_list']
#     args_to_check = item['kwargs']
#     resp_to_check = answer_match.group(1)
    
#     # print('=====test=====')
#     # print(resp_to_check)
#     # print('=====test=====')

#     is_following_list = []
#     for ids, arg in zip(ids_to_check, args_to_check):
        
#         instruction_cls = instructions_registry.INSTRUCTION_DICT[ids]
#         instruction = instruction_cls(ids)
#         call_build_description(instruction, arg)
        
#         if resp_to_check.strip() and instruction.check_following(resp_to_check):
#             is_following_list.append(True)
#         else:
#             is_following_list.append(False)
            
#     # Normalize the score to be between 0 and 1
#     score = is_following_list.count(True) / len(is_following_list)
    
#     score1=score

#     all_right=0
#     if score == 1:
#         all_right=1
    
#     return all_right,is_following_list.count(True),len(is_following_list),score1


#**************************Instructor Training**************************

import re
import os
import json
import requests
import sys
import threading
import inspect
from modules import instructions_registry
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

REWARD_SAMPLES_LOG_PATH = "if_reward1.jsonl"

_IF_VERIFER_LOG_LOCK = threading.Lock()
_REWARD_SAMPLES_LOG_LOCK = threading.Lock()

FILTER_VLLM_BASE_URL = os.getenv("FILTER_VLLM_BASE_URL", os.getenv("VLLM_BASE_URL", "http://YOUR_VLLM_HOST:55333/v1"))
FILTER_VLLM_MODEL = os.getenv("FILTER_VLLM_MODEL", os.getenv("VLLM_MODEL", "if-filter"))
FILTER_VLLM_API_KEY = os.getenv("FILTER_VLLM_API_KEY", os.getenv("VLLM_API_KEY", "EMPTY"))

ANSWER_VLLM_BASE_URL = os.getenv("ANSWER_VLLM_BASE_URL", os.getenv("VLLM_BASE_URL", "http://YOUR_VLLM_HOST:55222/v1"))
ANSWER_VLLM_MODEL = os.getenv("ANSWER_VLLM_MODEL", os.getenv("VLLM_MODEL", "if-answer"))
ANSWER_VLLM_API_KEY = os.getenv("ANSWER_VLLM_API_KEY", os.getenv("VLLM_API_KEY", "EMPTY"))

JUDGE_VLLM_BASE_URL = os.getenv("JUDGE_VLLM_BASE_URL", os.getenv("VLLM_BASE_URL", "http://YOUR_VLLM_HOST:55111/v1"))
JUDGE_VLLM_MODEL = os.getenv("JUDGE_VLLM_MODEL", os.getenv("VLLM_MODEL", "if-judge"))
JUDGE_VLLM_API_KEY = os.getenv("JUDGE_VLLM_API_KEY", os.getenv("VLLM_API_KEY", "EMPTY"))

def call_build_description(obj, args):

    method_signature = inspect.signature(obj.build_description)
    valid_params = set(method_signature.parameters.keys())

    filtered_args = {k: v for k, v in args.items() if k in valid_params}
    return obj.build_description(**filtered_args)
    
def _call_vllm_chat(
    messages: list[dict],
    base_url: str,
    api_key: str,
    model: str,
    max_tokens: int = 8192,
):
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        generated_text = resp.choices[0].message.content
        answer_match11 = re.search(r"</think>\n(.*)", generated_text, re.DOTALL)
        if answer_match11:
            generated_text = answer_match11.group(1)
        return generated_text
    except Exception:
        url = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=120)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            sys.exit(0)
        except requests.exceptions.RequestException:
            sys.exit(0)

        if r.status_code in (429, 502, 503, 504):
            sys.exit(0)

        r.raise_for_status()
        data = r.json()
        generated_text = data["choices"][0]["message"]["content"]
        answer_match11 = re.search(r"</think>\n(.*)", generated_text, re.DOTALL)
        if answer_match11:
            generated_text = answer_match11.group(1)
        return generated_text

def _parse_binary_judgement(text: str | None):
    if not text:
        return None
    s = str(text).strip()
    m = re.search(r"\[\[(\d+)\]\]", s)
    if m:
        try:
            v = int(m.group(1))
            return 1 if v == 1 else 0
        except Exception:
            return None
    m = re.search(r"\b([01])\b", s)
    if m:
        return int(m.group(1))
    m = re.search(r"([01])", s)
    if m:
        return int(m.group(1))
    return None

def _build_filter_prompt(seed_prompt: str, constraints: list[str], instruction: str | None = None):
    seed_prompt = (seed_prompt or "").strip()
    instruction = (instruction or "").strip()
    constraints = [str(c).strip() for c in (constraints or []) if str(c).strip()]

    constraints_block = "\n".join([f"- {c}" for c in constraints])
    prompt_template = (
        "# Role\n"
        "You are an “Instruction Constraint Consistency Reviewer”. Your task is to determine whether a given set of instructions/constraints contains **intrinsic logical conflicts** (that is, whether it is impossible to satisfy all requirements simultaneously without adding extra information while strictly following the constraints).\n\n"
        "# Core Principles (Very Important)\n"
        "- You should judge a conflict only when there is a “provable logical contradiction / mutually exclusive constraints”.\n"
        "- “High difficulty”, “tight word limit”, “large amount of information”, “may be poorly written / not detailed enough”, etc. are only feasibility challenges and do not constitute conflicts.\n"
        "- As long as there exists one possible output that can satisfy all constraints simultaneously, you must output [[1]].\n"
        "- Only when you can clearly identify at least one pair of constraints that are mutually exclusive in formal logic and cannot both be true should you output [[0]].\n\n"
        "# Judgment Criteria (Judge as conflict if any one condition is met)\n"
        "- **Mutually Exclusive Property Conflict**: the same output property is required to take mutually exclusive values  \n"
        "  Example: requiring “all lowercase” while also requiring a word that must be capitalized; requiring “no punctuation” while also requiring comma separation.\n"
        "- **Structure / Format Conflict**: the output structure cannot satisfy all requirements simultaneously  \n"
        "  Example: requiring “only one sentence” while also requiring “three paragraphs, each starting with a different vowel”.\n"
        "- **Language Conflict**: mutually exclusive languages or character rules are required at the same time  \n"
        "  Example: requiring “must be in Chinese” while also requiring “must be in English and all lowercase”.\n"
        "- **Exact Phrase Match Conflict**: requiring the exact inclusion of a phrase with fixed capitalization/punctuation while also requiring changes to its capitalization/punctuation or to the global format  \n"
        "  Example: requiring “the entire text must be lowercase” while also requiring the exact phrase 'You cannot wash away your sins' with an uppercase Y and no variants allowed.\n"
        "- **Quantity / Source Impossibility**: the required number of output items cannot be extracted from the input, while introducing new words/entities is prohibited  \n"
        "  Example: requiring “exactly 4 coreference words”, but the original sentence contains fewer than 4 words referring to the same entity, and external knowledge or newly introduced words are prohibited.\n\n"
        "# Non-Conflict Example Types (Do NOT judge as conflicts)\n"
        "- A low word limit without requiring an impossible amount of information, such as summarizing plot and character development within 100 words, is a compressible writing requirement and should be considered satisfiable by default.\n"
        "- Fixed opening and ending phrases together with paragraph requirements are satisfiable by default, as long as the phrases can be placed at the beginning of the first paragraph and the end of the last paragraph.\n\n"
        "# Output Format (Think first, then answer)\n"
        "Your output must contain two parts, in the following order:\n\n"
        "1) analysis:  \n"
        "Briefly explain in 1–5 sentences the key constraints you checked and whether they constitute a conflict. Line breaks are allowed.\n\n"
        "2) final:  \n"
        "Output only one label:  \n"
        "- If a conflict exists: [[0]]  \n"
        "- If no conflict exists: [[1]]\n\n"
        "# Output Constraints (Additional requirements for [[0]])\n"
        "- If you output [[0]], your analysis must clearly state which two or more constraints are mutually exclusive and why they cannot be satisfied simultaneously.\n"
        "- If you can only say “difficult / tight / may be impossible”, but cannot identify a mutually exclusive pair of constraints, you must output [[1]].\n\n"
        "---\n\n"
        "# Few-shot Examples  \n\n"
        "## Example 1 (Conflict: case exclusivity)\n"
        "Input:\n"
        "Generate three paragraphs of text, separated by ***; the entire text must be lowercase; the second paragraph must start with Agreement.\n"
        "Output:\n"
        "analysis:\n"
        "The text is required to be entirely lowercase, but the second paragraph must start with “Agreement”, which requires an uppercase initial letter.\n"
        "These two constraints are mutually exclusive and cannot be satisfied simultaneously.\n"
        "final:\n"
        "[[0]]\n\n"
        "## Example 2 (Conflict: punctuation exclusivity)\n"
        "Input:\n"
        "The output must not contain any punctuation; please separate three entity names with commas.\n"
        "Output:\n"
        "analysis:\n"
        "Prohibiting all punctuation also prohibits commas.\n"
        "However, the instruction requires commas to separate the entities, which is a direct conflict.\n"
        "final:\n"
        "[[0]]\n\n"
        "## Example 3 (No conflict: can be satisfied simultaneously)\n"
        "Input:\n"
        "Rewrite the sentence in passive voice; split it into two sentences; the total length must be exactly 30 English words; use a formal academic tone.\n"
        "Output:\n"
        "analysis:\n"
        "Passive voice, a two-sentence structure, a formal academic tone, and a 30-word limit can be satisfied simultaneously through precise wording.\n"
        "There are no mutually exclusive constraints.\n"
        "final:\n"
        "[[1]]\n\n"
        "## Example 4 (No conflict: paragraphs and bullet points can coexist)\n"
        "Input:\n"
        "Output 2 bullet points, each starting with -; do not use commas anywhere; include the phrase \\\"data science\\\" at least once.\n"
        "Output:\n"
        "analysis:\n"
        "Two markdown bullet points can be written clearly without relying on commas.\n"
        "Including the phrase and avoiding commas are not contradictory.\n"
        "final:\n"
        "[[1]]\n\n"
        "## Example 5 (No conflict: many requirements and tight word limit, but still logically satisfiable)\n"
        "Input:\n"
        "Write a book review in exactly two paragraphs; the total length must not exceed 100 words; include at least three plot points and their impacts; analyze at least two main character developments; begin with the phrase 'in the dystopian world of'; end with 'reflect on'; do not mention film adaptations or sequels.\n"
        "Output:\n"
        "analysis:\n"
        "Although the word limit is tight and there are many content requirements, there are no mutually exclusive conditions; all requirements may still be satisfied through concise summarization and precise expression.\n"
        "Therefore, this does not constitute a logical conflict.\n"
        "final:\n"
        "[[1]]\n\n"
        "---\n\n"
        "# Now process the real input\n"
        "Please only judge whether the following “real input” contains constraint conflicts. Use it only for judgment and do not rewrite it:\n\n"
        "Real input: {input}\n\n"
        "Please strictly follow the “Output Format (Think first, then answer)”.\n"
    )

    return prompt_template.replace("{input}", instruction)


def _build_judge_prompt(instruction: str, constraint: str, answer: str):
    few_shot_examples = """## Examples:

### Example 1:
[Reply]
Kathy and Sue are the two characters in this story.
[Constraint]
The response should include at least three characters from the story.
[Analysis]
The reply mentions only "Kathy" and "Sue", which is 2 characters. The constraint requires at least 3 characters.
NOT SATISFIED [[0]]

### Example 2:
[Reply]
Kathy
Sue
John
[Constraint]
The response should include at least three characters from the story.
[Analysis]
The reply mentions "Kathy", "Sue", and "John", which is 3 characters. This satisfies the constraint.
SATISFIED [[1]]

### Example 3:
[Reply]
The characters in this story are Kathy and Sue.
Kathy is mentioned in multiple sentences.
Sue appears in the conflict described.
[Constraint]
Each character's name must appear in a different paragraph.
[Analysis]
The reply has 3 paragraphs: 1) "The characters in this story are Kathy and Sue." 2) "Kathy is mentioned..." 3) "Sue appears..."
Each paragraph contains a character name.
SATISFIED [[1]]

### Example 4:
[Reply]
Kathy and Sue are friends. They talk every day.
[Constraint]
Each character's name must appear in a different paragraph.
[Analysis]
The reply has only 1 paragraph. Both character names appear in the same paragraph.
NOT SATISFIED [[0]]

### Example 5:
[Reply]
The answer is five.
[Constraint]
The response must include the word 'count' exactly once.
[Analysis]
The reply does not contain the word "count".
NOT SATISFIED [[0]]

### Example 6:
[Reply]
Let me count the items for you.
[Constraint]
The response must include the word 'count' exactly once.
[Analysis]
The reply contains "count" exactly once in "Let me count". No other occurrences of "count".
SATISFIED [[1]]

### Example 7:
[Reply]
I will count the number of items. Please count them carefully.
[Constraint]
The response must include the word 'count' exactly once.
[Analysis]
The reply contains "count" twice: "I will count" and "Please count them". This is more than once.
NOT SATISFIED [[0]]

### Example 8:
[Reply]
Kathy Sue John
[Constraint]
The response should not use any commas.
[Analysis]
The reply contains no commas, only spaces between the names.
SATISFIED [[1]]

### Example 9:
[Reply]
Kathy, Sue, and John are the characters.
[Constraint]
The response should not use any commas.
[Analysis]
The reply contains commas: "Kathy, Sue, and John".
NOT SATISFIED [[0]]

"""
    
    return (
        "Please judge whether the given reply follows the constraint(s). "
        "Analyze each constraint one by one and determine if it is satisfied.\n"
        f"{few_shot_examples}"
        "Now judge the following:\n"
        "[Reply]\n"
        f"{answer}\n"
        "[Constraint]\n"
        f"{constraint}\n"
        "Output your analysis and then the final score in [[score]] format. "
        "If ALL constraints are satisfied output [[1]] otherwise output [[0]]."
    )

def _append_jsonl(path: str, obj: dict):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass

    try:
        line = json.dumps(obj, ensure_ascii=False)
    except Exception:
        return

    try:
        with _IF_VERIFER_LOG_LOCK:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        return

def _append_reward_sample(obj: dict):
    if not REWARD_SAMPLES_LOG_PATH:
        return
    try:
        os.makedirs(os.path.dirname(REWARD_SAMPLES_LOG_PATH), exist_ok=True)
    except Exception:
        pass

    try:
        line = json.dumps(obj, ensure_ascii=False)
    except Exception:
        return

    try:
        with _REWARD_SAMPLES_LOG_LOCK:
            with open(REWARD_SAMPLES_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        return

def _truncate_text(text: str | None, max_chars: int = 8000):
    if text is None:
        return None
    s = str(text)
    if len(s) <= max_chars:
        return s
    return s[:max_chars]

def _extract_answer_content(answer: str):
    pattern = re.compile(r"<think>.*?</think>\s*<answer>(.*?)</answer>", re.DOTALL)
    answer_match = re.fullmatch(pattern, answer)
    #answer_match = re.search(r"</think>\n(.*)", answer, re.DOTALL)
    if answer_match:
        return answer_match.group(1)
    return None

def _parse_constraints_json(text: str):
    if not text:
        return None

    code_block_pattern = r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```"
    match = re.search(code_block_pattern, text, re.DOTALL)
    
    content_to_parse = match.group(1) if match else text.strip()

    try:
        obj = json.loads(content_to_parse)
    except Exception:
        try:
            start_idx = min(content_to_parse.find('{') if '{' in content_to_parse else len(content_to_parse),
                            content_to_parse.find('[') if '[' in content_to_parse else len(content_to_parse))
            end_idx = max(content_to_parse.rfind('}') , content_to_parse.rfind(']'))
            
            if start_idx < end_idx:
                obj = json.loads(content_to_parse[start_idx:end_idx+1])
            else:
                return None
        except Exception:
            return None

    if isinstance(obj, dict):
        constraints = [str(v).strip() for v in obj.values() if isinstance(v, (str, int, float)) and str(v).strip()]
        return constraints if constraints else None

    if isinstance(obj, list):
        constraints = [str(v).strip() for v in obj if isinstance(v, (str, int, float)) and str(v).strip()]
        return constraints if constraints else None

    return None

def _build_multi_constraint_question(prompt: str, constraints: list[str]) -> str:
    prompt = (prompt or "").strip()
    parts = []
    if prompt:
        parts.append(prompt)
    if constraints:
        parts.extend([str(c).strip() for c in constraints if str(c).strip()])
    return "\n".join(parts).strip()

def instruction_compute_score(answers, items):
    n_items = len(items)
    final_scores = [0.0] * n_items
    processed_items = set()

    resp_list = [None] * n_items
    extracted_constraints_list = [None] * n_items
    generated_answers = [None] * n_items

    reward_records = [None] * n_items
    if REWARD_SAMPLES_LOG_PATH:
        for item_idx, (answer, item) in enumerate(zip(answers, items)):
            reward_records[item_idx] = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "item_idx": item_idx,
                "prompt": _truncate_text(item.get("prompt", ""), 8000),
                "answer_raw": _truncate_text(answer, 8000),
            }

    for item_idx, (answer, item) in enumerate(zip(answers, items)):
        resp_to_check = _extract_answer_content(answer)
        resp_list[item_idx] = resp_to_check
        if resp_to_check is None:
            if reward_records[item_idx] is not None:
                reward_records[item_idx]["status"] = "extract_answer_failed"
            continue

        extracted_constraints = _parse_constraints_json(resp_to_check)
        if extracted_constraints:
            extracted_constraints_list[item_idx] = extracted_constraints
            if reward_records[item_idx] is not None:
                reward_records[item_idx]["status"] = "constraints_parsed"
                reward_records[item_idx]["constraints"] = [
                    _truncate_text(c, 500) for c in (extracted_constraints or [])
                ]
        else:
            final_scores[item_idx] = 0.0
            if reward_records[item_idx] is not None:
                reward_records[item_idx]["status"] = "constraints_parse_failed"
            continue

    instructions = [None] * n_items
    for item_idx in range(n_items):
        constraints = extracted_constraints_list[item_idx]
        if not constraints:
            continue
        prompt = items[item_idx].get("prompt", "")
        instructions[item_idx] = _build_multi_constraint_question(prompt, constraints)

    filter_results = [None] * n_items
    filter_futures = {}
    if any((idx not in processed_items) and instructions[idx] for idx in range(n_items)):
        with ThreadPoolExecutor(max_workers=200) as executor:
            for item_idx in range(n_items):
                if item_idx in processed_items:
                    continue
                instruction = instructions[item_idx]
                if not instruction:
                    continue
                if not (FILTER_VLLM_BASE_URL and FILTER_VLLM_MODEL):
                    filter_results[item_idx] = 1
                    continue
                seed_prompt = items[item_idx].get("prompt", "")
                constraints = extracted_constraints_list[item_idx] or []
                q = _build_filter_prompt(seed_prompt, constraints, instruction=instruction)
                filter_futures[
                    executor.submit(
                        _call_vllm_chat,
                        [{"role": "user", "content": q}],
                        FILTER_VLLM_BASE_URL,
                        FILTER_VLLM_API_KEY,
                        FILTER_VLLM_MODEL,
                        8192,
                    )
                ] = item_idx

            for future in as_completed(filter_futures):
                item_idx = filter_futures[future]
                try:
                    text = future.result()
                    filter_results[item_idx] = _parse_binary_judgement(text)
                except Exception:
                    filter_results[item_idx] = None

    for item_idx in range(n_items):
        if item_idx in processed_items:
            continue
        instruction = instructions[item_idx]
        constraints = extracted_constraints_list[item_idx]
        if not instruction or not constraints:
            continue

        ok = filter_results[item_idx]
        if ok != 1:
            final_scores[item_idx] = 0.0
            if reward_records[item_idx] is not None:
                reward_records[item_idx]["status"] = "filtered_out"
                reward_records[item_idx]["filter_result"] = ok

    answer_futures = {}
    if any(
        (idx not in processed_items)
        and instructions[idx]
        and extracted_constraints_list[idx]
        and filter_results[idx] == 1
        for idx in range(n_items)
    ):
        with ThreadPoolExecutor(max_workers=200) as executor:
            for item_idx in range(n_items):
                if item_idx in processed_items:
                    continue
                if filter_results[item_idx] != 1:
                    continue
                instruction = instructions[item_idx]
                if not instruction:
                    continue
                if not (ANSWER_VLLM_BASE_URL and ANSWER_VLLM_MODEL):
                    generated_answers[item_idx] = ""
                    continue
                answer_futures[
                    executor.submit(
                        _call_vllm_chat,
                        [{"role": "user", "content": instruction}],
                        ANSWER_VLLM_BASE_URL,
                        ANSWER_VLLM_API_KEY,
                        ANSWER_VLLM_MODEL,
                        8192,
                    )
                ] = item_idx

            for future in as_completed(answer_futures):
                item_idx = answer_futures[future]
                try:
                    generated_answers[item_idx] = future.result() or ""
                    if reward_records[item_idx] is not None:
                        reward_records[item_idx]["generated_answer"] = _truncate_text(
                            generated_answers[item_idx], 4000
                        )
                except Exception:
                    generated_answers[item_idx] = ""
                    if reward_records[item_idx] is not None:
                        reward_records[item_idx]["answer_error"] = True

    judge_futures = {}
    judge_results: dict[tuple[int, int], int | None] = {}
    if any(
        (idx not in processed_items)
        and instructions[idx]
        and extracted_constraints_list[idx]
        and filter_results[idx] == 1
        and (generated_answers[idx] is not None)
        for idx in range(n_items)
    ):
        with ThreadPoolExecutor(max_workers=200) as executor:
            for item_idx in range(n_items):
                if item_idx in processed_items:
                    continue
                if filter_results[item_idx] != 1:
                    continue
                instruction = instructions[item_idx]
                constraints = extracted_constraints_list[item_idx]
                answer_text = (generated_answers[item_idx] or "").strip()
                if not instruction or not constraints or not answer_text:
                    continue
                if not (JUDGE_VLLM_BASE_URL and JUDGE_VLLM_MODEL):
                    for ci in range(len(constraints)):
                        judge_results[(item_idx, ci)] = None
                    continue

                for ci, constraint in enumerate(constraints):
                    q = _build_judge_prompt(instruction, constraint, answer_text)
                    judge_futures[
                        executor.submit(
                            _call_vllm_chat,
                            [{"role": "user", "content": q}],
                            JUDGE_VLLM_BASE_URL,
                            JUDGE_VLLM_API_KEY,
                            JUDGE_VLLM_MODEL,
                            8192,
                        )
                    ] = (item_idx, ci)

            for future in as_completed(judge_futures):
                key = judge_futures[future]
                try:
                    text = future.result()
                    judge_results[key] = _parse_binary_judgement(text)
                except Exception:
                    judge_results[key] = None

    for item_idx in range(n_items):
        if item_idx in processed_items:
            continue
        if filter_results[item_idx] != 1:
            continue

        constraints = extracted_constraints_list[item_idx]
        if not constraints:
            continue
        answer_text = (generated_answers[item_idx] or "").strip()
        if not answer_text:
            final_scores[item_idx] = 0.0
            if reward_records[item_idx] is not None:
                reward_records[item_idx]["status"] = "empty_answer"
            continue

        n_cons = len(constraints)
        if n_cons <= 0:
            final_scores[item_idx] = 0.0
            continue

        ok_cnt = 0
        for ci in range(n_cons):
            v = judge_results.get((item_idx, ci), None)
            if v == 1:
                ok_cnt += 1

        adherence_rate = ok_cnt / n_cons
        final_scores[item_idx] = float(1.0 - adherence_rate)
        if reward_records[item_idx] is not None:
            reward_records[item_idx]["status"] = "judged"
            reward_records[item_idx]["constraints_followed"] = int(ok_cnt)
            reward_records[item_idx]["constraints_total"] = int(n_cons)
            reward_records[item_idx]["adherence_rate"] = float(adherence_rate)
            reward_records[item_idx]["reward"] = float(final_scores[item_idx])

    if REWARD_SAMPLES_LOG_PATH:
        for item_idx in range(n_items):
            rec = reward_records[item_idx]
            if rec is None:
                continue
            if "reward" not in rec:
                rec["reward"] = float(final_scores[item_idx])
            _append_reward_sample(rec)

    return final_scores

def instruction_val_compute_score(answer, item):
    pattern = re.compile(r"<think>.*?</think>\s*<answer>(.*?)</answer>", re.DOTALL)
    answer_match = re.fullmatch(pattern, answer)
    #answer_match = re.search(r"</think>\n(.*)", answer, re.DOTALL)
    
    if not answer_match:
        return 0,0,len(item),0
    
    ids_to_check = item['instruction_id_list']
    args_to_check = item['kwargs']
    resp_to_check = answer_match.group(1)
    
    is_following_list = []
    for ids, arg in zip(ids_to_check, args_to_check):
        
        instruction_cls = instructions_registry.INSTRUCTION_DICT[ids]
        instruction = instruction_cls(ids)
        call_build_description(instruction, arg)
        
        if resp_to_check.strip() and instruction.check_following(resp_to_check):
            is_following_list.append(True)
        else:
            is_following_list.append(False)
            
    score = is_following_list.count(True) / len(is_following_list)
    
    score1=score

    all_right=0
    if score == 1:
        all_right=1
    
    return all_right,is_following_list.count(True),len(is_following_list),score1