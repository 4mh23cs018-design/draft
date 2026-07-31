from typing import List, Dict, Any

class PromptBuilder:
    """Constructs grounded RAG prompts with strict source citation constraints."""

    SYSTEM_PROMPT = (
        "You are a helpful assistant.\n\n"
        "Answer ONLY from the supplied context.\n\n"
        "If the answer is not present, clearly say you don't know.\n\n"
        "Always cite the source."
    )

    @classmethod
    def build_prompt(cls, question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Formats context chunks into prompt structure matching required format.
        """
        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            filename = chunk.get("filename", "Unknown Document")
            page = chunk.get("page_number", 1)
            content = chunk.get("content", "").strip()
            context_blocks.append(
                f"[{idx}] Source: {filename} (Page {page})\n{content}"
            )

        context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."

        formatted_prompt = (
            f"{cls.SYSTEM_PROMPT}\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question:\n{question}"
        )

        return formatted_prompt
