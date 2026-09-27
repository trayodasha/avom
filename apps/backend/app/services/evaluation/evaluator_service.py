import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import EvaluationDataset, EvaluationExample
from app.models.evaluation import EvaluationRun, EvaluationResultItem, EvaluationStatus
from app.schemas.query import RAGConfiguration
from app.services.rag_pipeline import RAGPipelineService
from app.services.evaluation.metrics import RetrievalMetrics
from app.services.evaluation.judge import LLMJudge

logger = logging.getLogger(__name__)


class EvaluatorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag_service = RAGPipelineService(db)

    async def create_run(
        self,
        project_id: str,
        dataset_id: str,
        name: Optional[str] = None,
        configuration: Optional[RAGConfiguration] = None
    ) -> EvaluationRun:
        config = configuration or RAGConfiguration()
        run_name = name or f"Eval Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"

        # Fetch dataset examples count
        stmt = select(EvaluationExample).where(EvaluationExample.dataset_id == dataset_id)
        res = await self.db.execute(stmt)
        examples = res.scalars().all()

        run = EvaluationRun(
            project_id=project_id,
            dataset_id=dataset_id,
            name=run_name,
            status=EvaluationStatus.PENDING,
            configuration_snapshot=config.model_dump(),
            aggregate_metrics={},
            total_examples=len(examples),
            processed_examples=0,
            duration_ms=0.0
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def execute_run(self, run_id: str) -> EvaluationRun:
        stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
        res = await self.db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            raise ValueError(f"EvaluationRun {run_id} not found")

        run.status = EvaluationStatus.RUNNING
        await self.db.commit()

        start_time = time.time()

        try:
            # Fetch examples
            ex_stmt = select(EvaluationExample).where(EvaluationExample.dataset_id == run.dataset_id)
            ex_res = await self.db.execute(ex_stmt)
            examples = ex_res.scalars().all()

            config = RAGConfiguration(**run.configuration_snapshot)
            judge = LLMJudge(model_name=config.llm_model)

            metric_accumulators: Dict[str, List[float]] = {
                "recall@k": [],
                "precision@k": [],
                "mrr": [],
                "hit_rate@k": [],
                "ndcg@k": [],
                "faithfulness": [],
                "answer_relevance": [],
                "context_recall": [],
                "latency_ms": [],
            }

            for example in examples:
                ex_start = time.time()
                # Run RAG query
                query_res = await self.rag_service.execute_query(
                    project_id=run.project_id,
                    query=example.query,
                    config=config
                )

                retrieved_chunk_ids = [c.chunk_id for c in query_res.retrieved_chunks]
                retrieved_texts = [c.text for c in query_res.retrieved_chunks]
                gt_chunk_ids = example.ground_truth_chunk_ids or []

                # Compute retrieval metrics
                k = config.final_context_k or 5
                rec = RetrievalMetrics.recall_at_k(retrieved_chunk_ids, gt_chunk_ids, k=k)
                prec = RetrievalMetrics.precision_at_k(retrieved_chunk_ids, gt_chunk_ids, k=k)
                mrr_score = RetrievalMetrics.mrr(retrieved_chunk_ids, gt_chunk_ids)
                hit_score = RetrievalMetrics.hit_rate_at_k(retrieved_chunk_ids, gt_chunk_ids, k=k)
                ndcg_score = RetrievalMetrics.ndcg_at_k(retrieved_chunk_ids, gt_chunk_ids, k=k)

                # Compute generation metrics
                faith_score = await judge.evaluate_faithfulness(
                    question=example.query,
                    answer=query_res.answer,
                    context_chunks=retrieved_texts
                )
                rel_score = await judge.evaluate_answer_relevance(
                    question=example.query,
                    answer=query_res.answer
                )
                ctx_recall_score = await judge.evaluate_context_recall(
                    ground_truth=example.ground_truth,
                    context_chunks=retrieved_texts
                )

                item_latency = round((time.time() - ex_start) * 1000, 2)

                item_scores = {
                    "recall@k": rec,
                    "precision@k": prec,
                    "mrr": mrr_score,
                    "hit_rate@k": hit_score,
                    "ndcg@k": ndcg_score,
                    "faithfulness": faith_score,
                    "answer_relevance": rel_score,
                    "context_recall": ctx_recall_score,
                }

                # Record in accumulators
                for key, val in item_scores.items():
                    metric_accumulators[key].append(val)
                metric_accumulators["latency_ms"].append(item_latency)

                result_item = EvaluationResultItem(
                    run_id=run.id,
                    example_id=example.id,
                    query=example.query,
                    ground_truth=example.ground_truth,
                    generated_answer=query_res.answer,
                    retrieved_chunk_ids=retrieved_chunk_ids,
                    scores=item_scores,
                    latency_ms=item_latency,
                    tokens=query_res.tokens
                )
                self.db.add(result_item)
                run.processed_examples += 1

            # Compute aggregate averages
            aggregate_scores = {}
            for metric, values in metric_accumulators.items():
                aggregate_scores[metric] = round(sum(values) / len(values), 4) if values else 0.0

            run.aggregate_metrics = aggregate_scores
            run.status = EvaluationStatus.COMPLETED
            run.duration_ms = round((time.time() - start_time) * 1000, 2)
            run.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.exception(f"Evaluation run failed: {e}")
            run.status = EvaluationStatus.FAILED
            run.error_message = str(e)
            run.duration_ms = round((time.time() - start_time) * 1000, 2)

        await self.db.commit()
        await self.db.refresh(run)
        return run
