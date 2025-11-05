"""
Risk Assessment Service

Analyzes tender documents for risks and generates risk reports.
"""
import os
from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.tenderiq.db.tenderiq_repository import TenderIQRepository
from app.modules.tenderiq.services.document_parser import DocumentParser
from app.modules.tenderiq.services.tender_info_extractor import TenderInfoExtractor
from app.modules.tenderiq.services.scope_work_analyzer import ScopeOfWorkAnalyzer
from app.modules.tenderiq.services.advanced_intelligence import EnhancedRiskEngine
from app.modules.tenderiq.models.pydantic_models import (
    RiskAssessmentResponse,
    RiskDetailResponse,
)


class RiskAssessmentService:
    """Service for risk assessment of tenders"""

    def __init__(self):
        pass

    async def assess_risks(
        self,
        db: Session,
        tender_id: UUID,
        depth: str = "summary",
        include_historical: bool = False,
    ) -> RiskAssessmentResponse:
        """
        Perform on-demand risk assessment by running a partial analysis pipeline.
        """
        # 1. Fetch tender and document path
        repo = TenderIQRepository(db)
        tender = repo.get_tender_by_id(tender_id)
        if not tender or not tender.files:
            raise ValueError("Tender or associated documents not found.")
        file_path = tender.files[0].dms_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found at path: {file_path}")

        # 2. Parse document text
        doc_parser = DocumentParser()
        raw_text, _, _ = await doc_parser._extract_text(file_path)

        # 3. Extract necessary information for risk assessment
        info_extractor = TenderInfoExtractor()
        scope_analyzer = ScopeOfWorkAnalyzer()
        risk_engine = EnhancedRiskEngine()

        tender_info = await info_extractor.extract_tender_info(db, uuid4(), raw_text)
        financial_info = await info_extractor.extract_financial_info(raw_text)
        scope_data = await scope_analyzer.analyze_scope(db, uuid4(), raw_text)

        # 4. Assess risks
        risk_assessment = await risk_engine.assess_risks(
            tender_info=tender_info.model_dump(),
            scope_data=scope_data,
            financials=financial_info.model_dump(),
        )

        # 5. Map result to response model
        risk_details = [
            RiskDetailResponse(
                id=uuid4(),
                level=risk.get("severity", "medium").lower(),
                category=risk.get("category", "operational").lower(),
                title=risk.get("factor", "Untitled Risk"),
                description=risk.get("impact", ""),
                impact=risk.get("severity", "medium").lower(),
                likelihood=str(risk.get("likelihood", "medium")),
                mitigation_strategy=", ".join(risk_assessment.get("mitigation_strategies", [])),
                recommended_action="Review mitigation strategies.",
                related_documents=[],
            )
            for risk in risk_assessment.get("individual_risks", [])
        ]

        return RiskAssessmentResponse(
            tender_id=tender_id,
            overall_risk_level=risk_assessment.get("risk_level", "medium").lower(),
            risk_score=int(risk_assessment.get("overall_score", 50)),
            executive_summary=f"On-demand risk assessment completed. Risk level determined to be {risk_assessment.get('risk_level', 'MEDIUM')}.",
            risks=risk_details,
            analyzed_at=datetime.utcnow(),
        )

    def categorize_risk(self, risk_description: str) -> str:
        """
        Categorize a risk into one of: regulatory, financial, operational, contractual, market

        Uses keyword matching for now. TODO: Upgrade to LLM-based categorization.

        Args:
            risk_description: Description of the risk

        Returns:
            Risk category string
        """
        description_lower = risk_description.lower()

        # Keyword-based categorization (can be upgraded to LLM)
        category_keywords = {
            "regulatory": ["compliance", "legal", "regulation", "statute", "license", "permit", "approval"],
            "financial": ["cost", "budget", "price", "value", "payment", "cash flow", "revenue", "expense"],
            "operational": ["timeline", "deadline", "resource", "capacity", "schedule", "delivery", "performance"],
            "contractual": ["liability", "obligation", "penalty", "clause", "terms", "conditions", "agreement"],
            "market": ["competition", "demand", "supply", "price volatility", "market", "customer", "risk"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return category

        # Default to operational if no match
        return "operational"

    def calculate_risk_score(self, risks: List[dict]) -> int:
        """
        Calculate overall risk score (0-100) from identified risks.

        Weighted by level and likelihood:
        - Critical + High likelihood = 10 points
        - High + Medium likelihood = 6 points
        - etc.

        Args:
            risks: List of identified risks

        Returns:
            Risk score from 0-100
        """
        if not risks:
            return 0

        level_scores = {
            "critical": 10,
            "high": 6,
            "medium": 3,
            "low": 1,
        }

        likelihood_multipliers = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4,
        }

        total_score = 0
        for risk in risks:
            level = risk.get("level", "medium").lower() if isinstance(risk.get("level"), str) else "medium"
            likelihood = risk.get("likelihood", "medium").lower() if isinstance(risk.get("likelihood"), str) else "medium"

            # Get scores with defaults
            level_score = level_scores.get(level, 3)
            likelihood_mult = likelihood_multipliers.get(likelihood, 0.7)

            total_score += level_score * likelihood_mult

        # Normalize to 0-100 range
        # Max score = 10 risks * 10 points * 1.0 = 100
        # But cap at 100
        return min(int(total_score * 10), 100)

    def generate_mitigations(self, risk_description: str) -> str:
        """
        Generate mitigation strategies for a risk.

        TODO: Use LLM to generate better mitigations.

        Args:
            risk_description: Description of the risk

        Returns:
            Suggested mitigation strategy
        """
        description_lower = risk_description.lower()

        # Template-based mitigations (can be upgraded to LLM)
        if "deadline" in description_lower or "timeline" in description_lower:
            return "Establish internal project milestones, allocate dedicated team, prioritize critical tasks"
        elif "cost" in description_lower or "budget" in description_lower or "price" in description_lower:
            return "Conduct detailed cost analysis, identify cost-saving opportunities, negotiate better rates with suppliers"
        elif "requirement" in description_lower or "complexity" in description_lower:
            return "Break down complex requirements into smaller components, conduct feasibility study, allocate expert resources"
        elif "compliance" in description_lower or "legal" in description_lower:
            return "Engage legal counsel, ensure full understanding of regulations, establish compliance tracking mechanisms"
        elif "resource" in description_lower or "capacity" in description_lower:
            return "Assess resource availability, consider outsourcing, hire additional staff if needed"
        else:
            return "Conduct further analysis, engage subject matter experts, develop contingency plans"

    # ==================== Helper Methods ====================

    def _determine_risk_level(self, impact: str, likelihood: str) -> str:
        """
        Determine risk level based on impact and likelihood.

        Matrix:
        - High impact + High likelihood = Critical
        - High impact + Medium likelihood = High
        - etc.
        """
        impact_score = {"high": 3, "medium": 2, "low": 1}.get(impact.lower(), 2)
        likelihood_score = {"high": 3, "medium": 2, "low": 1}.get(likelihood.lower(), 2)

        combined_score = impact_score * likelihood_score

        if combined_score >= 8:
            return "critical"
        elif combined_score >= 5:
            return "high"
        elif combined_score >= 3:
            return "medium"
        else:
            return "low"

    def _score_to_level(self, score: int) -> str:
        """Convert numeric score to risk level"""
        if score >= 75:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        else:
            return "low"

    def _generate_executive_summary(self, risks: List, risk_score: int) -> str:
        """Generate executive summary of risks"""
        if not risks:
            return "No significant risks identified in tender analysis."

        risk_counts = {}
        for risk in risks:
            level = risk.level.value if hasattr(risk.level, 'value') else str(risk.level)
            risk_counts[level] = risk_counts.get(level, 0) + 1

        summary_parts = [f"Risk score: {risk_score}/100. "]

        if risk_counts.get("critical", 0) > 0:
            summary_parts.append(f"{risk_counts['critical']} critical risk(s) identified that require immediate attention. ")
        if risk_counts.get("high", 0) > 0:
            summary_parts.append(f"{risk_counts['high']} high risk(s) identified. ")

        summary_parts.append("Refer to detailed risk list for mitigation strategies.")

        return "".join(summary_parts)

    def _get_recommended_action(self, risk_title: str) -> str:
        """Get recommended action for specific risk"""
        title_lower = risk_title.lower()

        actions = {
            "deadline": "Immediately establish project timeline and resource allocation plan",
            "complex": "Conduct comprehensive requirements analysis and feasibility study",
            "cost": "Perform detailed cost estimation and budget planning",
            "resource": "Assess team capacity and hire or outsource as needed",
            "compliance": "Engage legal and compliance team to review requirements",
            "financial": "Review financial viability and secure adequate funding",
        }

        for keyword, action in actions.items():
            if keyword in title_lower:
                return action

        return "Establish risk monitoring and mitigation plan"
