
TASK_DESCRIPTION_TEMPLATE_SOFT = """1. I currently have a seed question, but the seed questions are relatively simple. To make the instructions more complex,
I want you to identify and return five atomic constraints that can be added to the seed question.
2. I will provide [Seed Question] and [Constraint References], and you can use these references to propose five constraints
that would increase the difficulty of the seed question.
3. [Constraint References] are just suggestions. You may choose one or more constraints from the list or propose new
ones if needed.
4. Do not modify or rewrite the seed question. Your task is only to generate new constraints that can be added to it.
5. Return the added constraints in the following JSON format:
json
{{
"c1": "<the content of first constraint>",
"c2": "<the content of second constraint>",
"c3": "<the content of third constraint>",
"c4": "<the content of fourth constraint>",
"c5": "<the content of fifth constraint>"
}}
6. Do not return anything else. No explanation, no reformulated question, no analysisâ€”only the JSON structure.

[Constraint References]  
1. Lexical content constraint : Mandatory use of specific terms or symbols, including their inclusion and precise placement. Example: "...must include the word 'beautiful.'"  
2. Element constraint : Mandates for including specific elements or concepts in responses, reflecting a scenario or object. Example: "...highlights the Great Wall."  
3. Semantic constraint : Directives on thematic content, perspective, or tone, emphasizing response significance. Example: "Write a poem about London."  
4. Word Count : Limit the number of words or tokens. Example: "A 50-word poem."  
5. Sentence Count : Limit the number of sentences. Example: "...three sentences."  
6. Paragraph Count : Limit the number of paragraphs. Example: "divided into 3 sections."  
7. Document Count : Limit the number of documents. Example: "...list 3 articles."  
8. Tone and emotion : The emotional tone must adhere to standards such as seriousness, anger, joy, humor, and politeness. Example: "Write a letter in an angry and sarcastic tone."  
9. Form and style : Text expression standards ensure alignment with specific stylistic criteria in both presentation and perception. Example: "Write a passage in an encyclopedic style."  
10. Audience-specific : Text should be tailored to specific audiences, ensuring clarity and relevance for children, students, or specialized groups. Example: "Write a poem for a 6-year-old."  
11. Authorial style : Texts should emulate the styles of authors like Shakespeare to achieve artistic effects or depth. Example: "Write a passage in the style of Shakespeare."  
12. Fundamental format : Widely accepted and utilized standard formats, including JSON, XML, LaTeX, HTML, Table, and Markdown. Example: "Extract keywords and output in JSON format."  
13. Bespoke format : Protocols for information expression tailored to specific needs, including paragraphing, headings, text emphasis, examples, and bullet points. Example: "Summarize the main idea and output in unordered list format"  
14. Specialized format : Formatting standards tailored for specialized applications or domains. Example: "Conform to electronic medical record format."  
15. Pragmatic constraint : Contextual language study, encompassing speech acts, implicature, discourse, dialects, sociolects, and language policy. Example: "Output in English, classical Chinese style."  
16. Syntactic constraint : Sentence structure, including phrases, constituents, subordinate clauses, ba-constructions, and imperatives. Example: "Use imperatives with nouns and verb phrases."  
17. Morphological constraint : The internal structure and formation rules of words, including roots, affixes, and morphological changes. Example: "Output all content in lowercase English."  
18. Phonological constraint : Study on phonological structures: phonemes, allophones, pitch, duration, and intensity. Example: "Single-rhyme tongue twisters."  
19. Role-based constraint : Simulating characters based on context, emulating their traits, language, and behaviors. Example: "You are Confucius, how do you decide?"  
20. Task-specific constraint : Offer tailored solutions based on a nuanced understanding of situational demands. Example: "Must work from home, how to report?"  
21. Complex context constraint : Reasoning and problem-solving within intricate and multifaceted form. Example: "4 on the left, 10 total, which from right?"  
22. Example constraint : Regulate new responses by leveraging intrinsic patterns from a limited set of samples. Example: "Example: input:xxx, output:(...); input:xx, output?"  
23. Inverse constraint : Narrow the response space through inverse constraints and indirect exclusion. Example: "Prohibited from answer political topics."  
24. Contradictory constraint : Mutually exclusive constraints prevent fulfilling all requirements concurrently. Example: "Write a five-character quatrain, 1000 words."  
25. Rule constraint : Standardize the road of responses through meticulously crafted logic flows or actions. Example: "Each answer adds 1, 1+1=3, then 2+3=?"

[Seed Question]
{seed_question}
"""


TASK_DESCRIPTION_TEMPLATE_HARD = """
1. I currently have a seed question, but the seed questions are relatively simple. To make the instructions more complex,
I want you to identify and return three atomic constraints that can be added to the seed question.

2. I will provide [Seed Question] and [Constraint References], and you can use these references to propose three constraints
that would increase the difficulty of the seed question.

3. You may refer to the [Constraint References] below to design constraints. These references are only suggestions.
You may choose one or more constraints from the list or propose new ones if needed.


Diversity Requirement:
(1) You must select exactly one constraint from three different categories.
(2) You are NOT allowed to generate two constraints from the same category.

Intra-Category Subtype Diversity Requirement (IMPORTANT):
For each category, you must first choose exactly one subtype from the subtype list of that category.
Then you must generate the constraint using ONLY that chosen subtype.
To reduce repetition, you must avoid always choosing the easiest subtype. Prefer less frequently used subtypes when possible.


Constraint Compatibility Rules (IMPORTANT):
When generating the constraints, you must ensure that they do not conflict with each other. 
Avoid selecting constraint subtypes that would make the response logically impossible or structurally incompatible. The following incompatibility rules must be respected:

1. JSON Structure Conflicts
If the constraint requires the entire response to be valid JSON, do NOT combine it with constraints that enforce:
- bullet points
- highlighted spans
- sectioned structures
- paragraph count
- sentence count
- title wrappers
- multiple responses
These formats usually break valid JSON structure.

2. Paragraph Structure Conflicts
Do NOT combine paragraph-related constraints that enforce different structures. Specifically avoid combining:
- paragraph count
- nth paragraph first word
- sentence count

3. Language and Case Conflicts
Language constraints must not contradict each other. Avoid combinations such as:
- Response Language (e.g., Chinese) with English ALL CAPS
- Response Language (e.g., Chinese) with English all lowercase
- English ALL CAPS together with English all lowercase

4. Formatting Wrapper Conflicts
Avoid combining wrappers that compete for the entire output structure, such as:
- Title Wrapper
- Quotation Wrapper
- JSON Output

5. Special Pattern Conflicts
Constraints that enforce global response patterns should not be combined with many other structural constraints. Avoid combining:
- Two Distinct Responses
- Repeat-Then-Answer
with strict formatting or layout constraints such as JSON Output, Bullet Points Count, or Sectioned Structure.

6. Punctuation Restrictions
If the constraint forbids commas (No Commas), avoid requiring phrases or keywords that naturally contain commas.

7. Word-Length and Structure Conflicts
Avoid combining strict word count limits with structural constraints that would likely require more words, such as:
- bullet point lists
- multiple sections
- repeated responses.


Constraint Wording Requirement:
Each constraint must be written as a complete natural-language instruction sentence. Start the sentence with phrases such as "The response should...", "Your answer must...",
or "The response should...". Avoid shorthand or parameter-style expressions such as: "Response Language: zh", "No Commas", or "Exactly 3 paragraphs".
Each constraint should be a clear and self-contained instruction sentence.


Constraint Categories:

Category A â€?Lexical Constraints
- Required Keywords
- Keyword Frequency
- Forbidden Words
- Letter Frequency
- ALL-CAPS Word Frequency

Category B â€?Structural Layout Constraints
- Sentence Count
- Paragraph Count
- Bullet Points Count
- Sectioned Structure
- Nth Paragraph First Word
- Word Count

Category C â€?Formatting Constraints
- Highlighted Spans
- Title Wrapper
- Quotation Wrapper
- JSON Output

Category D â€?Language Style Constraints
- Response Language
- English ALL CAPS
- English all lowercase
- No Commas

Category E â€?Special Pattern Constraints
- Repeat-Then-Answer
- Exact Ending Phrase
- Two Distinct Responses
- Postscript
- Placeholder Count

4. Do not modify or rewrite the seed question. Your task is only to generate new constraints that can be added to it.

5. Return the added constraints in the following JSON format:
json
{{
  "c1": "<the content of first constraint>",
  "c2": "<the content of second constraint>",
  "c3": "<the content of third constraint>"
}}

6. Do not return anything else. No explanation, no reformulated question, no analysisâ€”only the JSON structure.
7. Do NOT output the category name or subtype name; only output the constraint text itself.

[Constraint References]
1. Required Keywords â€?Include given keywords in the response.
2. Keyword Frequency â€?A specified keyword must appear a certain number of times, with a relation like "less than" or "at least".
3. Forbidden Words â€?Do not include any of the given forbidden words.
4. Letter Frequency â€?A specified letter must appear a certain number of times, with a relation like "less than" or "at least".
5. Response Language â€?Your ENTIRE response must be in the specified language (e.g., "english", "chinese").
6. Sentence Count â€?Your response must contain a number of sentences subject to "less than" or "at least".
7. Paragraph Count â€?There must be exactly N paragraphs separated by the markdown divider "***".
8. Word Count â€?Answer with a number of words subject to "less than" or "at least".
9. Nth Paragraph First Word â€?There must be exactly N paragraphs separated by "\n\n", and paragraph K must start with the specified first word.
10. Placeholder Count â€?The response must contain at least N placeholders in square brackets, such as [address].
11. Postscriptâ€?At the end of the response, explicitly add a postscript starting with a marker like "P.S." or "P.P.S".
12. Bullet Points Count â€?The answer must contain exactly N bullet points using markdown bullets starting with "*" or "-".
13. Highlighted Spans â€?Highlight at least N sections in the answer using markdown emphasis like *highlight* or **highlight**.
14. Sectioned Structure â€?The response must have at least N sections, each beginning with "Section X" or "SECTION X".
15. JSON Output â€?Entire output must be valid JSON (optionally wrapped in markdown code fences).
16. Title Wrapper â€?The answer must contain a title wrapped in double angle brackets, such as <<poem of joy>>.
17. Two Distinct Responses â€?Give two different responses; responses and only responses should be separated by exactly "******".
18. Repeat-Then-Answer â€?First repeat the request word-for-word without change, then give your answer.
19. Exact Ending Phrase â€?Finish your response with the exact given phrase; no other words should follow.
20. ALL-CAPS Word Frequency â€?Words in ALL CAPS should appear a certain number of times with relation "less than" or "at least".
21. English ALL CAPS â€?Your entire response should be in English, and in ALL CAPITAL letters.
22. English all lowercase â€?Your entire response should be in English, and in all lowercase letters; no capital letters allowed.
23. No Commas â€?In your entire response, refrain from the use of any commas.
24. Quotation Wrapper â€?Wrap your entire response with double quotation marks.

[Seed Question]
{seed_question}
"""


import math
import os
from collections import defaultdict
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch
from datasets import load_dataset
from PIL import Image
from PIL.Image import Image as ImageObject
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizer, ProcessorMixin

from ..models.transformers.qwen2_vl import get_rope_index
from . import torch_functional as VF


def collate_fn(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    tensors = defaultdict(list)
    non_tensors = defaultdict(list)
    for feature in features:
        for key, value in feature.items():
            if isinstance(value, torch.Tensor):
                tensors[key].append(value)
            else:
                non_tensors[key].append(value)

    for key, value in tensors.items():
        tensors[key] = torch.stack(value, dim=0)

    for key, value in non_tensors.items():
        non_tensors[key] = np.array(value, dtype=object)

    return {**tensors, **non_tensors}


def process_image(image: Union[Dict[str, Any], ImageObject], max_pixels: int, min_pixels: int) -> ImageObject:
    if isinstance(image, dict):
        image = Image.open(BytesIO(image["bytes"]))

    if (image.width * image.height) > max_pixels:
        resize_factor = math.sqrt(max_pixels / (image.width * image.height))
        width, height = int(image.width * resize_factor), int(image.height * resize_factor)
        image = image.resize((width, height))

    if (image.width * image.height) < min_pixels:
        resize_factor = math.sqrt(min_pixels / (image.width * image.height))
        width, height = int(image.width * resize_factor), int(image.height * resize_factor)
        image = image.resize((width, height))

    if image.mode != "RGB":
        image = image.convert("RGB")

    return image

#**************************Instructor Training**************************

class RLHFDataset(Dataset):
    """
    We assume the dataset contains a column that contains prompts and other information
    """

    def __init__(
        self,
        data_path: str,
        tokenizer: PreTrainedTokenizer,
        processor: Optional[ProcessorMixin],
        prompt_key: str = "prompt",
        # answer_key: str = "answer",
        image_key: str = "images",
        max_prompt_length: int = 1024,
        truncation: str = "error",
        system_prompt: str = "",
        max_pixels: int = None,
        min_pixels: int = None,
    ):
        self.tokenizer = tokenizer
        self.processor = processor
        self.prompt_key = prompt_key
        # self.answer_key = answer_key
        self.image_key = image_key
        self.max_prompt_length = max_prompt_length
        self.truncation = truncation
        self.max_pixels = max_pixels
        self.min_pixels = min_pixels

        if "@" in data_path:
            data_path, data_split = data_path.split("@")
        else:
            data_split = "train"

        if os.path.isdir(data_path):
            self.dataset = load_dataset("parquet", data_dir=data_path, split="train")
        elif os.path.isfile(data_path):
            self.dataset = load_dataset("parquet", data_files=data_path, split="train")
        else:  # remote dataset
            self.dataset = load_dataset(data_path, split=data_split)

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        row_dict: dict = self.dataset[index]

        import random
        
        task_description = random.choice(
            [TASK_DESCRIPTION_TEMPLATE_HARD, TASK_DESCRIPTION_TEMPLATE_SOFT]
        ).format(seed_question=row_dict[self.prompt_key])



        messages = [{"role": "user", "content": task_description}]

        
        messages.insert(0, {"role": "system", "content": "Output your answer strictly following the format: <think> [your step-by-step analysis] </think><answer>[your answer]</answer>"})
        
        prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)


        if self.image_key in row_dict:
            prompt = prompt.replace("<image>", "<|vision_start|><|image_pad|><|vision_end|>")
            row_dict["multi_modal_data"] = {
                "image": [
                    process_image(image, self.max_pixels, self.min_pixels) for image in row_dict.pop(self.image_key)
                ]
            }
            model_inputs = self.processor(row_dict["multi_modal_data"]["image"], prompt, return_tensors="pt")
            input_ids = model_inputs.pop("input_ids")[0]
            attention_mask = model_inputs.pop("attention_mask")[0]
            row_dict["multi_modal_inputs"] = dict(model_inputs)
            position_ids = get_rope_index(
                self.processor,
                input_ids=input_ids,
                image_grid_thw=model_inputs["image_grid_thw"],
                attention_mask=attention_mask,
            )  # (3, seq_length)
        else:
            model_inputs = self.tokenizer([prompt], add_special_tokens=False, return_tensors="pt")
            input_ids = model_inputs.pop("input_ids")[0]
            attention_mask = model_inputs.pop("attention_mask")[0]
            position_ids = torch.clip(attention_mask.cumsum(dim=0) - 1, min=0, max=None)  # (seq_length,)

        input_ids, attention_mask, position_ids = VF.postprocess_data(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            max_length=self.max_prompt_length,
            pad_token_id=self.tokenizer.pad_token_id,
            left_pad=True,
            truncation=self.truncation,
        )
        row_dict["input_ids"] = input_ids
        row_dict["attention_mask"] = attention_mask
        row_dict["position_ids"] = position_ids
        row_dict["raw_prompt_ids"] = self.tokenizer.encode(prompt, add_special_tokens=False)
    
        
        row_dict["ground_truth"] = {
            "prompt": row_dict[self.prompt_key],
        }
        return row_dict



# # **************************Follower Training**************************
# class RLHFDataset(Dataset):
#     """
#     We assume the dataset contains a column that contains prompts and other information
#     """

#     def __init__(
#         self,
#         data_path: str,
#         tokenizer: PreTrainedTokenizer,
#         processor: Optional[ProcessorMixin],
#         prompt_key: str = "prompt",
#         image_key: str = "images",
#         max_prompt_length: int = 1024,
#         truncation: str = "error",
#         system_prompt: str = "",
#         max_pixels: int = None,
#         min_pixels: int = None,
#     ):
#         self.tokenizer = tokenizer
#         self.processor = processor
#         self.prompt_key = prompt_key
#         self.image_key = image_key
#         self.max_prompt_length = max_prompt_length
#         self.truncation = truncation
#         self.max_pixels = max_pixels
#         self.min_pixels = min_pixels

#         if "@" in data_path:
#             data_path, data_split = data_path.split("@")
#         else:
#             data_split = "train"

#         if os.path.isdir(data_path):
#             self.dataset = load_dataset("parquet", data_dir=data_path, split="train")
#         elif os.path.isfile(data_path):
#             self.dataset = load_dataset("parquet", data_files=data_path, split="train")
#         else:  # remote dataset
#             self.dataset = load_dataset(data_path, split=data_split)

#     def __len__(self):
#         return len(self.dataset)

#     def __getitem__(self, index):
#         row_dict: dict = self.dataset[index]

        
#         messages = [{"role": "user", "content": row_dict[self.prompt_key]}]
        
#         messages.insert(0, {"role": "system", "content": "Output your answer strictly following the format: <think> [your step-by-step analysis] </think><answer>[your answer]</answer>"})
        
#         prompt = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)


#         if self.image_key in row_dict:
#             prompt = prompt.replace("<image>", "<|vision_start|><|image_pad|><|vision_end|>")
#             row_dict["multi_modal_data"] = {
#                 "image": [
#                     process_image(image, self.max_pixels, self.min_pixels) for image in row_dict.pop(self.image_key)
#                 ]
#             }
#             model_inputs = self.processor(row_dict["multi_modal_data"]["image"], prompt, return_tensors="pt")
#             input_ids = model_inputs.pop("input_ids")[0]
#             attention_mask = model_inputs.pop("attention_mask")[0]
#             row_dict["multi_modal_inputs"] = dict(model_inputs)
#             position_ids = get_rope_index(
#                 self.processor,
#                 input_ids=input_ids,
#                 image_grid_thw=model_inputs["image_grid_thw"],
#                 attention_mask=attention_mask,
#             )  # (3, seq_length)
#         else:
#             model_inputs = self.tokenizer([prompt], add_special_tokens=False, return_tensors="pt")
#             input_ids = model_inputs.pop("input_ids")[0]
#             attention_mask = model_inputs.pop("attention_mask")[0]
#             position_ids = torch.clip(attention_mask.cumsum(dim=0) - 1, min=0, max=None)  # (seq_length,)

#         input_ids, attention_mask, position_ids = VF.postprocess_data(
#             input_ids=input_ids,
#             attention_mask=attention_mask,
#             position_ids=position_ids,
#             max_length=self.max_prompt_length,
#             pad_token_id=self.tokenizer.pad_token_id,
#             left_pad=True,
#             truncation=self.truncation,
#         )
#         row_dict["input_ids"] = input_ids
#         row_dict["attention_mask"] = attention_mask
#         row_dict["position_ids"] = position_ids
#         row_dict["raw_prompt_ids"] = self.tokenizer.encode(prompt, add_special_tokens=False)
#         try:
#             instruction_id_list = row_dict.pop('instruction_id_list')
#             kwargs = row_dict.pop('kwargs')
#             constraints = row_dict.pop('constraint')
#         except KeyError as e:
#             print("\n[DATASET ERROR]")
#             print(f"Index: {index}")
#             print(f"Missing key: {e}")
#             print("Available keys:", row_dict.keys())
#             print("Row content:", row_dict)
#             raise

        
#         row_dict["ground_truth"] = {
#             "instruction_id_list": instruction_id_list,
#             "kwargs": kwargs,
#             "prompt": row_dict[self.prompt_key],
#             "constraints": constraints
#         }
#         return row_dict
