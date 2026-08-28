import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai


class LLMJudge:
    """Uses Gemini as an independent judge for Task 1 and Task 2 outputs."""

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash-lite",
        )

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=self.api_key)

    def judge(
        self,
        case: dict[str, Any],
        model_output: Any,
    ) -> dict[str, Any]:

        prompt = f"""
You are an independent evaluator for an AI support automation system.

Judge the system output using ONLY the supplied evaluation case
and system output. Do not invent facts.

Evaluate:

1. Factual correctness
2. Grounding in the provided information
3. Completeness
4. Correct interpretation of the task
5. Overall usefulness

Evaluation case:

{json.dumps(case, indent=2, default=str)}

System output:

{json.dumps(model_output, indent=2, default=str)}

Return ONLY valid JSON using exactly this structure:

{{
    "score": 0.0,
    "verdict": "PASS",
    "reasoning": "Brief explanation of the evaluation."
}}

Rules:

- score must be between 0.0 and 1.0
- verdict must be PASS or FAIL
- PASS means the output is sufficiently correct and useful
- FAIL means there is a significant correctness, grounding,
  or completeness problem
- Do not invent information that is not present in the case
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
            },
        )

        try:
            result = json.loads(response.text.strip())

        except json.JSONDecodeError as exc:
            raise ValueError("Gemini judge returned invalid JSON.") from exc

        score = result.get("score")
        verdict = result.get("verdict")
        reasoning = result.get("reasoning")

        if not isinstance(score, (int, float)) or not 0.0 <= float(score) <= 1.0:
            raise ValueError("Gemini judge returned an invalid score.")

        if verdict not in {"PASS", "FAIL"}:
            raise ValueError("Gemini judge returned an invalid verdict.")

        if not isinstance(reasoning, str):
            raise ValueError("Gemini judge returned invalid reasoning.")

        return {
            "score": float(score),
            "verdict": verdict,
            "reasoning": reasoning,
        }


if __name__ == "__main__":
    print("LLM judge module loaded successfully.")
