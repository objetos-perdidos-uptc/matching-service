from typing import List
from app.domain.entities import MatchResult, Report
from app.domain.ports import IMatchRepository, IEventPublisher
from app.domain.services.scoring_engine import MatchingEngine

class EvaluateReportUseCase:
    def __init__(
        self,
        match_repository: IMatchRepository,
        event_publisher: IEventPublisher,
        matching_engine: MatchingEngine,
        weights: dict
    ):
        self.match_repository = match_repository
        self.event_publisher = event_publisher
        self.matching_engine = matching_engine
        self.weights = weights

    async def execute(self, target_report: Report, candidate_reports: List[Report]) -> List[MatchResult]:
        results: List[MatchResult] = []

        for candidate in candidate_reports:
            # ¡LA MAGIA ESTÁ AQUÍ!
            # Si el reporte que estamos evaluando es LOST, el candidato es FOUND.
            if target_report.report_type == ReportType.LOST:
                lost = target_report
                found = candidate
            else:
                # Si el reporte es FOUND, el candidato es el LOST.
                lost = candidate
                found = target_report

            result = self.matching_engine.calculate_match(lost, found, self.weights)
            results.append(result)

        results.sort(key=lambda x: x.total_score, reverse=True)
        await self.match_repository.save_many(results)

        for r in results:
            if r.total_score >= 80.0:
                await self.event_publisher.publish_high_match(user_id=lost.user_id, match_result=r)
                
        return results
