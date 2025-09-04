from app.services.llm_huggingface import HuggingFaceChat
from app.services.llm_openai import OpenAIChat
from app.core.config import settings
from app.services.searcher import CodeSearcher
from app.services.chunker import extract_chunks
from app.core.logger import logger
import os

class ChatService:
    def __init__(
        self,
        searcher: CodeSearcher,
        chunker,
        hf_chat: HuggingFaceChat,
        openai_chat: OpenAIChat
    ):
        self.searcher = searcher
        self.chunker = chunker
        self.hf_chat = hf_chat
        self.openai_chat = openai_chat

    def get_chat_backend(self):
        if settings.USE_OPENAI:
            logger.info("Using OpenAI backend for chat.")
            return self.openai_chat
        else:
            logger.info("Using HuggingFace backend for chat.")
            return self.hf_chat

    def combine_chunks(self, relevant_chunks) -> str:
        """Combine relevant chunks into a context string with better formatting."""
        context_parts = []
        total_length = 0
        max_length = 2000  # Reduced from 4000 to speed up inference

        for score, meta in relevant_chunks:
            try:
                with open(meta["path"], "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    chunk_code = "".join(lines[meta["start_line"] - 1 : meta["end_line"]])

                chunk_code = chunk_code.strip()
                # Better formatting with file info
                summary = f"=== From {meta['path']} (lines {meta['start_line']}-{meta['end_line']}) ===\n"
                summary += f"Type: {meta.get('type', 'unknown')}, Name: {meta.get('name', 'unknown')}\n\n"

                chunk_with_summary = summary + chunk_code + "\n\n"

                if total_length + len(chunk_with_summary) > max_length:
                    break

                context_parts.append(chunk_with_summary)
                total_length += len(chunk_with_summary)

            except Exception as e:
                logger.warning(f"Failed to read chunk from {meta['path']}: {e}")

        combined_context = "".join(context_parts) if context_parts else "No relevant code context found."

        # Log the context being sent to LLM for debugging
        logger.info(f"Combined context length: {len(combined_context)} characters")
        logger.info(f"Context preview: {combined_context[:300]}...")

        return combined_context


    def answer_question(self, repo_name: str, question: str) -> str:
        logger.info(f"Answering question for repo={repo_name}: {question}")
        relevant_chunks = self.searcher.semantic_search(repo_name, question, top_k=10)
        context = self.combine_chunks(relevant_chunks)
        backend = self.get_chat_backend()
        response = backend.chat(question, context)
        logger.info("Received response from LLM backend.")
        return response
