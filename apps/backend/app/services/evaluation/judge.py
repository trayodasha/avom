import re
import json
import logging
from typing import List, Dict, Any, Optional
from app.services.generation.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)


class LLMJudge:
    """
    LLM-as-a-judge evaluators for RAG generation assessment:
    - Faithfulness (Context Groundedness)
    - Answer Relevance (Query Alignment)
    - Context Recall (Ground Truth Context Coverage)
    - Context Precision (Signal-to-Noise in Retrieval Ordering)
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.provider = get_llm_provider(model_name)

    async def evaluate_faithfulness(
        self,
        question: str,
        answer: str,
        context_chunks: List[str]
    ) -> float:
        """
        Computes fraction of claims in generated answer that are directly supported
        by the retrieved context.
        """
        if not answer.strip() or not context_chunks:
            return 0.0

        full_context = "\n---\n".join(context_chunks)

        # Decompose answer into individual sentences / claims
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if len(s.strip()) > 8]
        if not sentences:
            return 1.0

        # Deterministic analysis fallback if using local provider or offline
        if getattr(self.provider, "provider_name", "") == "local":
            supported_count = 0
            context_words = set(re.findall(r'\b\w{3,}\b', full_context.lower()))
            for s in sentences:
                sent_words = set(re.findall(r'\b\w{3,}\b', s.lower()))
                overlap = len(sent_words.intersection(context_words))
                if len(sent_words) > 0 and (overlap / len(sent_words)) >= 0.4:
                    supported_count += 1
            return round(supported_count / len(sentences), 4)

        prompt = f"""You are an unbiased AI evaluation judge assessing the Faithfulness of a RAG response.
Evaluate whether each claim in the response is strictly supported by the provided context.

Context:
{full_context[:3000]}

Response:
{answer}

Instructions:
1. Break down the response into atomic claims.
2. Determine if each claim is supported (yes/no) by the context.
3. Return ONLY a valid JSON object in this exact schema:
{{"total_claims": <int>, "supported_claims": <int>, "faithfulness_score": <float between 0.0 and 1.0>, "reason": "<short explanation>"}}
"""
        try:
            res = await self.provider.generate(prompt=prompt, system_prompt="You are a strict evaluation judge. Output ONLY JSON.")
            data = json.loads(res.content.strip().replace("```json", "").replace("```", ""))
            return float(data.get("faithfulness_score", 0.0))
        except Exception as e:
            logger.warning(f"LLM faithfulness evaluation fallback: {e}")
            # Robust lexical overlap fallback
            context_words = set(re.findall(r'\b\w{3,}\b', full_context.lower()))
            supported = 0
            for s in sentences:
                sent_words = set(re.findall(r'\b\w{3,}\b', s.lower()))
                if sent_words and (len(sent_words.intersection(context_words)) / len(sent_words)) >= 0.35:
                    supported += 1
            return round(supported / len(sentences), 4)

    async def evaluate_answer_relevance(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Assesses how directly and completely the generated answer addresses the question.
        """
        if not answer.strip() or not question.strip():
            return 0.0

        if getattr(self.provider, "provider_name", "") == "local":
            # Semantic keyword overlap heuristic for local offline run
            q_words = set(re.findall(r'\b\w{3,}\b', question.lower()))
            a_words = set(re.findall(r'\b\w{3,}\b', answer.lower()))
            if not q_words:
                return 1.0
            overlap = len(q_words.intersection(a_words))
            return min(1.0, round(0.5 + (overlap / len(q_words)) * 0.5, 4))

        prompt = f"""You are an evaluation judge assessing Answer Relevance.
Evaluate how well the generated answer directly answers the user's question without adding irrelevant noise or evasion.

User Question: {question}
Generated Answer: {answer}

Return ONLY a JSON object:
{{"relevance_score": <float between 0.0 and 1.0>, "reason": "<brief justification>"}}
"""
        try:
            res = await self.provider.generate(prompt=prompt, system_prompt="You are a strict evaluation judge. Output ONLY JSON.")
            data = json.loads(res.content.strip().replace("```json", "").replace("```", ""))
            return float(data.get("relevance_score", 0.0))
        except Exception as e:
            logger.warning(f"LLM relevance evaluation fallback: {e}")
            q_words = set(re.findall(r'\b\w{3,}\b', question.lower()))
            a_words = set(re.findall(r'\b\w{3,}\b', answer.lower()))
            overlap = len(q_words.intersection(a_words))
            return min(1.0, round(0.5 + (overlap / len(q_words)) * 0.5, 4)) if q_words else 0.8

    async def evaluate_context_recall(
        self,
        ground_truth: str,
        context_chunks: List[str]
    ) -> float:
        """
        Evaluates whether the retrieved context contains all necessary information
        required to formulate the ground truth answer.
        """
        if not ground_truth.strip() or not context_chunks:
            return 0.0

        full_context = "\n---\n".join(context_chunks).lower()
        gt_words = set(re.findall(r'\b\w{3,}\b', ground_truth.lower()))
        if not gt_words:
            return 1.0

        found_words = sum(1 for w in gt_words if w in full_context)
        return round(found_words / len(gt_words), 4)
