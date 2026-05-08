TASK_DESCRIPTION_TEMPLATE_HARD = """
1. I currently have a seed question, but the seed questions are relatively simple. To make the instructions more complex,
I want you to identify and return five atomic constraints that can be added to the seed question.

2. I will provide [Seed Question] and [Constraint References], and you can use these references to propose five constraints
that would increase the difficulty of the seed question.

3. You may refer to the [Constraint References] below to design constraints. These references are only suggestions.
You may choose one or more constraints from the list or propose new ones if needed.

Additional Diversity Requirement:
(1) You must select exactly one constraint from each of the five categories (one per category).
(2) You are NOT allowed to generate two constraints from the same category.

Intra-Category Subtype Diversity Requirement (IMPORTANT):
For each category, you must first choose exactly one subtype from the subtype list of that category.
Then you must generate the constraint using ONLY that chosen subtype.
To reduce repetition, you must avoid always choosing the easiest subtype. Prefer less frequently used subtypes when possible.
Do NOT output the category name or subtype name; only output the constraint text itself.

Constraint Categories:

Category A â€?Lexical Constraints
- Required Keywords
- Keyword Frequency
- Forbidden Words
- Letter Frequency
- ALL-CAPS Word Frequency

Category B â€?Structural & Formatting Constraints
- Sentence Count
- Paragraph Count
- Bullet Points Count
- Sectioned Structure
- Nth Paragraph First Word
- Word Count
- Highlighted Spans
- Title Wrapper
- Quotation Wrapper

Category C â€?Language Style Constraints
- Response Language
- English ALL CAPS
- English all lowercase
- No Commas

Category D â€?Logical / Output Constraints
- JSON Output
- Fixed-Option Answer

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
  "c3": "<the content of third constraint>",
  "c4": "<the content of fourth constraint>",
  "c5": "<the content of fifth constraint>"
}}

6. Do not return anything else. No explanation, no reformulated question, no analysisâ€”only the JSON structure.

[Constraint References]
1. Required Keywords â€?Include given keywords in the response.
2. Keyword Frequency â€?A specified keyword must appear a certain number of times, with a relation like "less than" or "at least".
3. Forbidden Words â€?Do not include any of the given forbidden words.
4. Letter Frequency â€?A specified letter must appear a certain number of times, with a relation like "less than" or "at least".
5. Response Language â€?Your ENTIRE response must be in the specified language (e.g., "en", "zh").
6. Sentence Count â€?Your response must contain a number of sentences subject to "less than" or "at least".
7. Paragraph Count â€?There must be exactly N paragraphs separated by the markdown divider "***".
8. Word Count â€?Answer with a number of words subject to "less than" or "at least".
9. Nth Paragraph First Word â€?There must be exactly N paragraphs separated by "\n\n", and paragraph K must start with the specified first word.
10. Placeholder Count â€?The response must contain at least N placeholders in square brackets, such as [address].
11. Postscriptâ€?At the end of the response, explicitly add a postscript starting with a marker like "P.S." or "P.P.S".
12. Bullet Points Count â€?The answer must contain exactly N bullet points using markdown bullets starting with "*" or "-".
13. Fixed-Option Answer â€?Answer with one of the fixed allowed options (choose exactly one option).
14. Highlighted Spans â€?Highlight at least N sections in the answer using markdown emphasis like *highlight* or **highlight**.
15. Sectioned Structure â€?The response must have at least N sections, each beginning with "Section X" or "SECTION X".
16. JSON Output â€?Entire output must be valid JSON (optionally wrapped in markdown code fences).
17. Title Wrapper â€?The answer must contain a title wrapped in double angle brackets, such as <<poem of joy>>.
18. Two Distinct Responses â€?Give two different responses; responses and only responses should be separated by exactly "******".
19. Repeat-Then-Answer â€?First repeat the request word-for-word without change, then give your answer.
20. Exact Ending Phrase â€?Finish your response with the exact given phrase; no other words should follow.
21. ALL-CAPS Word Frequency â€?Words in ALL CAPS should appear a certain number of times with relation "less than" or "at least".
22. English ALL CAPS â€?Your entire response should be in English, and in ALL CAPITAL letters.
23. English all lowercase â€?Your entire response should be in English, and in all lowercase letters; no capital letters allowed.
24. No Commas â€?In your entire response, refrain from the use of any commas.
25. Quotation Wrapper â€?Wrap your entire response with double quotation marks.

[Seed Question]
{seed_question}
"""