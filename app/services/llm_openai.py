# app/llms/llm_openai.py

import openai
from app.core.config import settings
from app.core.logger import logger

class OpenAIChat:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.DEFAULT_LLM_MODEL

    def chat(self, question: str, context: str) -> str:
        logger.info(f"Calling OpenAI with model={self.model_name}")
        messages = [
            {"role": "system", "content": "You are a helpful code assistant."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"}
        ]

        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=messages,
            max_tokens=512,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
