import os
import re
import json
import argparse
import requests
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

_PROMPT_COUNT_LOCK = threading.Lock()
_PROMPT_COUNTS = {
    "soft": 0,
    "hard": 0,
}


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


VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:55111/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "EMPTY")
VLLM_MODEL = os.getenv("VLLM_MODEL", "if-verifer")

_JSONL_WRITE_LOCK = threading.Lock()


def _read_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                yield line_no, json.loads(s)
            except Exception:
                yield line_no, None


def _append_jsonl(path: str, obj: dict):
    with _JSONL_WRITE_LOCK:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _extract_json_object(text: str):
    if not text:
        return None

    text = text.strip()

    code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    m = re.search(code_block_pattern, text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            return json.loads(text[start : end + 1])
    except Exception:
        return None

    return None


def _normalize_constraints(obj, expected_keys: list[str]) -> list[str] | None:
    if not isinstance(obj, dict):
        return None

    constraints = []
    for k in expected_keys:
        v = obj.get(k)
        if isinstance(v, (str, int, float)):
            s = str(v).strip()
            if s:
                constraints.append(s)

    return constraints if len(constraints) == len(expected_keys) else None


def build_multi_constraint_instruction(seed_question: str, constraints: list[str]) -> str:
    seed_question = (seed_question or "").strip()
    parts = []
    if seed_question:
        parts.append(seed_question)
    if constraints:
        parts.extend([str(c).strip() for c in constraints if str(c).strip()])
    return "\n".join(parts).strip()


def call_vllm_chat(prompt: str, base_url: str = VLLM_BASE_URL, api_key: str = VLLM_API_KEY, model: str = VLLM_MODEL, max_tokens: int = 2048, timeout: int = 120):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    
    #add
    import re
    answer = data["choices"][0]["message"]["content"]
    answer_match = re.search(r"</think>\n(.*)", answer, re.DOTALL)
    if answer_match:
        return answer_match.group(1)
    else:
        return answer

    # return data["choices"][0]["message"]["content"]


def generate_constraints_from_seed(seed_question: str) -> dict:
    # template = random.choice([TASK_DESCRIPTION_TEMPLATE_HARD, TASK_DESCRIPTION_TEMPLATE_SOFT])
    # prompt = template.format(seed_question=seed_question)
    template = random.choice(
        [("hard", TASK_DESCRIPTION_TEMPLATE_HARD), ("soft", TASK_DESCRIPTION_TEMPLATE_SOFT)]
    )
    template_name, template_text = template

    with _PROMPT_COUNT_LOCK:
        _PROMPT_COUNTS[template_name] += 1

    prompt = template_text.format(seed_question=seed_question)

    raw = call_vllm_chat(prompt)
    obj = _extract_json_object(raw)
    expected_keys = ["c1", "c2", "c3"] if template_name == "hard" else ["c1", "c2", "c3", "c4", "c5"]
    constraints = _normalize_constraints(obj, expected_keys)
    if constraints is None:
        raise ValueError(f"Failed to parse constraints JSON with keys {', '.join(expected_keys)}")

    return {
        "seed_question": seed_question,
        "constraints": constraints,
        "constraints_json": obj,
        "multi_constraint_instruction": build_multi_constraint_instruction(seed_question, constraints),
        "raw_model_output": raw,
    }


def _build_item_no_decomposition(seed_question: str, constraints: list[str]) -> dict | None:
    seed_question = (seed_question or "").strip()
    constraints = [str(c).strip() for c in (constraints or []) if str(c).strip()]
    if not seed_question or not constraints:
        return None

    return {
        "seed_question": seed_question,
        "constraint": constraints,
        "prompt": build_multi_constraint_instruction(seed_question, constraints),
        "kwargs": [{"num_bullets": 3} for _ in range(len(constraints))],
        "instruction_id_list": ["soft" for _ in range(len(constraints))],
    }


def _process_one_jsonl_item(line_no: int, item, prompt_field: str, keep_input: bool) -> dict | None:
    if item is None:
        return None

    seed_question = item.get(prompt_field)
    if not isinstance(seed_question, str) or not seed_question.strip():
        return None

    try:
        result = generate_constraints_from_seed(seed_question)
        built = _build_item_no_decomposition(result["seed_question"], result["constraints"])
        return built
    except Exception:
        return None


def process_jsonl(
    input_jsonl: str,
    output_jsonl: str,
    prompt_field: str = "prompt",
    keep_input: bool = True,
    num_workers: int = 200,
    max_in_flight: int | None = None,
):
    if max_in_flight is None:
        max_in_flight = max(1, int(num_workers) * 2)

    futures = set()
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for line_no, item in _read_jsonl(input_jsonl):
            futures.add(executor.submit(_process_one_jsonl_item, line_no, item, prompt_field, keep_input))
            if len(futures) >= max_in_flight:
                done = next(as_completed(futures))
                futures.remove(done)
                out = done.result()
                if out is None:
                    continue
                if isinstance(out, list):
                    for rec in out:
                        if rec is not None:
                            _append_jsonl(output_jsonl, rec)
                else:
                    _append_jsonl(output_jsonl, out)

        for future in as_completed(futures):
            out = future.result()
            if out is None:
                continue
            if isinstance(out, list):
                for rec in out:
                    if rec is not None:
                        _append_jsonl(output_jsonl, rec)
            else:
                _append_jsonl(output_jsonl, out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed_question", type=str)
    parser.add_argument("--input_jsonl", type=str)
    parser.add_argument("--output_jsonl", type=str)
    parser.add_argument("--prompt_field", type=str, default="prompt")
    parser.add_argument("--no_keep_input", action="store_true")
    parser.add_argument("--num_workers", type=int, default=200)
    parser.add_argument("--print_raw", action="store_true")
    args = parser.parse_args()

    if args.input_jsonl:
        if not args.output_jsonl:
            raise SystemExit("--output_jsonl is required when using --input_jsonl")
        process_jsonl(
            args.input_jsonl,
            args.output_jsonl,
            prompt_field=args.prompt_field,
            keep_input=not args.no_keep_input,
            num_workers=args.num_workers,
        )
        print(
            json.dumps(
                {
                    "prompt_usage": _PROMPT_COUNTS
                },
                ensure_ascii=False
            )
        )
        return

    if not args.seed_question:
        raise SystemExit("Either --seed_question or --input_jsonl must be provided")

    result = generate_constraints_from_seed(args.seed_question)

    print(json.dumps(result["constraints_json"], ensure_ascii=False))
    print("\n" + result["multi_constraint_instruction"])

    if args.print_raw:
        print("\n--- RAW MODEL OUTPUT ---\n")
        print(result["raw_model_output"])




if __name__ == "__main__":
    main()
