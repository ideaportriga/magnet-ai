from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.evaluation.evaluation import Evaluation


class EvaluationsService(service.SQLAlchemyAsyncRepositoryService[Evaluation]):
    async def update_result_score(
        self,
        db_session,
        evaluation_id: str,
        result_id: str,
        score: float,
        score_comment: str | None = None,
    ) -> bool:
        """
        Update score and score_comment for a specific result in results (ORM way).
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[update_result_score] Called with evaluation_id={evaluation_id}, result_id={result_id}, score={score}, score_comment={score_comment}"
        )

        evaluation = await db_session.get(Evaluation, evaluation_id)
        if not evaluation:
            logger.warning(
                f"[update_result_score] Evaluation not found: {evaluation_id}"
            )
            return False
        if not evaluation.results:
            logger.warning(
                f"[update_result_score] Evaluation {evaluation_id} has no results"
            )
            return False

        updated = False
        for result in evaluation.results:
            if str(result.get("id")) == str(result_id):
                logger.info(
                    f"[update_result_score] Found result {result_id}, updating score and comment"
                )
                result["score"] = score
                result["score_comment"] = score_comment
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(evaluation, "results")
                updated = True
                break

        if updated:
            logger.info(
                f"[update_result_score] Committing changes for evaluation {evaluation_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_result_score] Result {result_id} not found in evaluation {evaluation_id}"
            )
        return updated

    """Evaluations service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Evaluation]):
        """Evaluations repository."""

        model_type = Evaluation

    repository_type = Repo
