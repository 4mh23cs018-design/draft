import time
from typing import List, Dict, Any

class EvaluationTracker:
    """Tracks latency metrics, token usage, and retrieval precision across chat requests."""

    _query_logs: List[Dict[str, Any]] = []
    _max_logs: int = 100

    @classmethod
    def calculate_precision_at_k(cls, chunks: List[Dict[str, Any]], threshold: float = 0.3) -> float:
        """Calculate Precision@K ratio of retrieved chunks exceeding relevance threshold."""
        if not chunks:
            return 0.0
        relevant = sum(1 for c in chunks if c.get("score", 0.0) >= threshold or c.get("rrf_score", 0.0) > 0)
        return round(relevant / len(chunks), 2)

    @classmethod
    def record_query(
        cls,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        retrieval_latency_ms: float,
        llm_latency_ms: float,
        total_latency_ms: float,
        token_usage: Dict[str, int]
    ) -> Dict[str, Any]:
        precision = cls.calculate_precision_at_k(retrieved_chunks)
        record = {
            "timestamp": time.time(),
            "question": question,
            "chunk_count": len(retrieved_chunks),
            "precision_at_k": precision,
            "retrieval_latency_ms": round(retrieval_latency_ms, 2),
            "llm_latency_ms": round(llm_latency_ms, 2),
            "total_latency_ms": round(total_latency_ms, 2),
            "token_usage": token_usage
        }

        cls._query_logs.append(record)
        if len(cls._query_logs) > cls._max_logs:
            cls._query_logs.pop(0)

        return record

    @classmethod
    def get_summary_metrics(cls) -> Dict[str, Any]:
        if not cls._query_logs:
            return {
                "total_queries": 0,
                "avg_retrieval_latency_ms": 0.0,
                "avg_llm_latency_ms": 0.0,
                "avg_total_latency_ms": 0.0,
                "avg_precision_at_k": 0.0,
                "total_tokens_consumed": 0,
                "recent_queries": []
            }

        total_q = len(cls._query_logs)
        avg_retrieval = sum(q["retrieval_latency_ms"] for q in cls._query_logs) / total_q
        avg_llm = sum(q["llm_latency_ms"] for q in cls._query_logs) / total_q
        avg_total = sum(q["total_latency_ms"] for q in cls._query_logs) / total_q
        avg_precision = sum(q["precision_at_k"] for q in cls._query_logs) / total_q
        total_tokens = sum(q["token_usage"].get("total_tokens", 0) for q in cls._query_logs)

        return {
            "total_queries": total_q,
            "avg_retrieval_latency_ms": round(avg_retrieval, 2),
            "avg_llm_latency_ms": round(avg_llm, 2),
            "avg_total_latency_ms": round(avg_total, 2),
            "avg_precision_at_k": round(avg_precision, 2),
            "total_tokens_consumed": total_tokens,
            "recent_queries": list(reversed(cls._query_logs[-10:]))
        }
