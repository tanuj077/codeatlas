# app/services/llm_huggingface.py (simple, fast version)

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from app.core.config import settings
from app.core.logger import logger
import torch

class HuggingFaceChat:
    def __init__(self):
        print(f"LLM model name is: {settings.LLM_MODEL_NAME}")
        model_name = settings.LLM_MODEL_NAME
        logger.info(f"Loading HuggingFace model: {model_name}")

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Using device: {device} for HuggingFace model.")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        use_device_map = False
        try:
            from accelerate import Accelerator
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto"
            )
            use_device_map = True
        except ImportError:
            logger.warning("Accelerate not installed. Falling back to basic loading without device_map.")
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.model.to(device)

        pipeline_kwargs = {}
        if not use_device_map:
            pipeline_kwargs["device"] = device

        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            **pipeline_kwargs
        )

    def chat(self, question: str, context: str, strict: bool = True) -> dict:
        """
        Generate a concise, developer-friendly, structured explanation for the given question + context.

        Returns a dict:
        {
            "answer": <cleaned explanation>,
            "tokens_used": <approx word count>
        }
        """

        import re

        # configurable word bounds (fallback to defaults)
        TARGET_MIN_WORDS = getattr(settings, "LLM_MIN_WORDS", 200)
        TARGET_MAX_WORDS = getattr(settings, "LLM_MAX_WORDS", 300)

        max_new_tokens = getattr(settings, "LLM_MAX_TOKENS", 600)

        prompt = f"""You are CodeAtlas, an expert technical assistant for developers.

            Answer every question in a **developer-friendly tone**:
            - concise, practical, no fluff
            - assume the reader is a developer, not a student
            - prefer code insights over theory
            - explain trade-offs or pitfalls when relevant

            Strict output structure (use these headers exactly, no extras):
            1. Purpose:
            2. How it works / integration:
            3. Design approach:

            Constraints:
            - Keep the explanation between {TARGET_MIN_WORDS} and {TARGET_MAX_WORDS} words.
            - Do NOT include full code blocks, file paths, or raw large snippets. Mention identifiers inline if useful.
            - Treat the CONTEXT below as background only; do not repeat it verbatim.
            - End your reply with the exact marker: [END_OF_ANSWER]

            CONTEXT (reference only, do not echo):
            {context}

            QUESTION:
            {question}

            Answer:
            """

        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": False,
            "temperature": 0.0,
        }
        try:
            if hasattr(self, "tokenizer") and getattr(self.tokenizer, "eos_token_id", None) is not None:
                gen_kwargs["pad_token_id"] = self.tokenizer.eos_token_id
        except Exception:
            pass

        logger.info("Calling HuggingFace model with max_new_tokens=%s", gen_kwargs["max_new_tokens"])
        result = self.pipe(prompt, **gen_kwargs)

        # ---- Step 1: Extract generated text robustly ----
        generated = ""
        if isinstance(result, list):
            generated = result[0].get("generated_text") or result[0].get("summary_text", "")
        elif isinstance(result, dict):
            generated = result.get("generated_text") or result.get("summary_text", "")
        generated = generated or ""

        # ---- Step 2: Remove echoed prompt safely ----
        if prompt in generated:
            generated = generated.split("Answer:", 1)[-1].strip()
        else:
            generated = re.sub(r"^.*Answer:\s*", "", generated, flags=re.DOTALL)

        # ---- Step 3: Normalize formatting ----
        text = generated.strip()
        lines = [ln.lstrip() for ln in text.splitlines()]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        # ---- Step 4: Enforce end marker if strict ----
        if "[END_OF_ANSWER]" in text:
            text = text.split("[END_OF_ANSWER]", 1)[0].strip()
        elif strict:
            logger.warning("Strict mode enabled but marker not found; using truncated output.")

        if not text:
            fallback = "I couldn't produce an explanation. Please try again with a shorter context."
            logger.warning("LLM returned empty response; returning fallback message.")
            return {"answer": fallback, "tokens_used": 0}

        return text














