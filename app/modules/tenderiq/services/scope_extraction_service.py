"""
Scope of Work Extraction Service

Extracts scope of work, deliverables, and effort estimation from tender documents.
"""
import os
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.modules.tenderiq.db.tenderiq_repository import TenderIQRepository
from app.modules.tenderiq.services.document_parser import DocumentParser
from app.modules.tenderiq.services.scope_work_analyzer import ScopeOfWorkAnalyzer
from app.modules.tenderiq.models.pydantic_models import (
    ScopeOfWorkResponse,
    ScopeOfWorkDetailResponse,
    WorkItemResponse,
    DeliverableResponse,
    KeyDatesResponse,
)


class ScopeExtractionService:
    """Service for extracting scope of work from tender documents"""

    def __init__(self):
        pass

    async def extract_scope(
        self,
        db: Session,
        tender_id: UUID,
    ) -> ScopeOfWorkResponse:
        """
        Perform on-demand scope of work extraction from tender documents.
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

        # 3. Analyze scope of work
        scope_analyzer = ScopeOfWorkAnalyzer()
        scope_data = await scope_analyzer.analyze_scope(db, uuid4(), raw_text)

        # 4. Map result to the response model
        work_items = [
            WorkItemResponse(
                id=uuid4(),
                description=item.get("description", "N/A"),
                estimated_duration=f"{item.get('estimatedDays', 0)} days",
                priority=item.get("complexity", "medium"),
                dependencies=[],
            )
            for item in scope_data.get("work_items", [])
        ]

        total_effort = scope_data.get("total_effort_days", 0)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=total_effort)
        key_dates = KeyDatesResponse(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        scope_detail = ScopeOfWorkDetailResponse(
            description="Scope of work extracted from tender document.",
            work_items=work_items,
            key_deliverables=[],  # New analyzer does not extract this directly
            estimated_total_effort=total_effort,
            estimated_total_duration=f"{scope_data.get('estimated_duration_months', 0)} months",
            key_dates=key_dates,
        )

        return ScopeOfWorkResponse(
            tender_id=tender_id,
            scope_of_work=scope_detail,
            analyzed_at=datetime.utcnow(),
        )

    def extract_work_items(self, scope_text: str) -> List[WorkItemResponse]:
        """
        Extract individual work items from scope description.

        Args:
            scope_text: Scope of work text

        Returns:
            List of work items with descriptions and dependencies
        """
        if not scope_text:
            return []

        work_items = []

        # Parse bullet points and numbered items
        lines = scope_text.split("\n")
        item_descriptions = []

        for line in lines:
            line_clean = line.strip()
            # Check if line starts with bullet or number
            if line_clean.startswith("-") or line_clean.startswith("•"):
                item_desc = line_clean.lstrip("-•").strip()
                if item_desc:
                    item_descriptions.append(item_desc)
            elif line_clean and not line_clean.startswith(" "):
                # Might be a paragraph, split by common keywords
                if any(keyword in line_clean.lower() for keyword in ["and", "with", ","]):
                    parts = [p.strip() for p in line_clean.split(" and ") + line_clean.split(",")]
                    item_descriptions.extend([p for p in parts if len(p) > 5])

        # Create work items (limit to 5-7 items for clarity)
        complexity_levels = {"Authentication": "high", "Authorization": "high", "Search": "medium",
                            "Backup": "medium", "Integration": "high", "Storage": "medium"}

        for i, item_desc in enumerate(item_descriptions[:7]):
            # Estimate duration (in days)
            estimated_duration = self._estimate_item_duration(item_desc)

            work_items.append(
                WorkItemResponse(
                    id=uuid4(),
                    description=item_desc,
                    estimated_duration=estimated_duration,
                    priority=self._determine_priority(i, len(item_descriptions)),
                    dependencies=[],
                )
            )

        return work_items

    def extract_deliverables(self, scope_text: str) -> List[DeliverableResponse]:
        """
        Extract key deliverables from scope description.

        Args:
            scope_text: Scope of work text

        Returns:
            List of deliverables with descriptions and dates
        """
        if not scope_text:
            return []

        deliverables = []

        # Common deliverable patterns
        deliverable_keywords = [
            "document", "report", "design", "specification", "manual",
            "code", "system", "framework", "API", "interface", "dashboard"
        ]

        text_lower = scope_text.lower()
        deliverable_list = []

        for keyword in deliverable_keywords:
            if keyword.lower() in text_lower:
                deliverable_list.append(f"{keyword.title()} Deliverable")

        # Add generic project deliverables
        base_deliverables = [
            "Technical Architecture Document",
            "System Implementation",
            "API Documentation",
            "User Guide and Training",
            "System Testing Report",
        ]

        for i, deliverable_name in enumerate(base_deliverables[:4]):
            # Calculate delivery date (spread over project timeline)
            delivery_offset_days = (i + 1) * 30

            deliverables.append(
                DeliverableResponse(
                    id=uuid4(),
                    description=deliverable_name,
                    delivery_date=(datetime.now() + timedelta(days=delivery_offset_days)).strftime("%Y-%m-%d"),
                    acceptance_criteria=[
                        f"{deliverable_name} reviewed and approved",
                        "All requirements met",
                        "Quality standards met",
                    ],
                )
            )

        return deliverables

    def estimate_effort(
        self,
        scope_text: str,
        work_items: List[WorkItemResponse]
    ) -> dict:
        """
        Estimate total effort and duration for the scope.

        Args:
            scope_text: Scope description
            work_items: Identified work items

        Returns:
            Dict with estimated_days, estimated_duration_text, complexity_level
        """
        if not scope_text:
            return {
                "estimated_days": 30,
                "estimated_duration_text": "1 month",
                "complexity_level": "medium",
            }

        # Count complexity indicators
        high_complexity_keywords = [
            "integration", "migration", "architecture", "security",
            "performance", "scalability", "disaster recovery", "compliance"
        ]

        complexity_score = sum(
            scope_text.lower().count(keyword) for keyword in high_complexity_keywords
        )

        # Estimate based on scope length and complexity
        word_count = len(scope_text.split())
        item_count = len(work_items) if work_items else 1

        # Base estimate: 10 days per work item + complexity bonus
        base_days = item_count * 10
        complexity_bonus = complexity_score * 5

        estimated_days = base_days + complexity_bonus

        # Determine complexity level
        if complexity_score >= 3:
            complexity_level = "high"
        elif complexity_score >= 1:
            complexity_level = "medium"
        else:
            complexity_level = "low"

        # Format duration text
        if estimated_days > 180:
            duration_text = f"{estimated_days // 30} months"
        elif estimated_days > 30:
            duration_text = f"{estimated_days // 7} weeks"
        else:
            duration_text = f"{estimated_days} days"

        return {
            "estimated_days": min(estimated_days, 365),  # Cap at 1 year
            "estimated_duration_text": duration_text,
            "complexity_level": complexity_level,
        }

    # ==================== Helper Methods ====================

    def _estimate_item_duration(self, item_description: str) -> str:
        """Estimate duration for a single work item"""
        desc_lower = item_description.lower()

        # High effort keywords
        high_effort = ["complex", "integration", "security", "performance", "migration"]
        medium_effort = ["module", "component", "interface", "specification"]
        low_effort = ["documentation", "testing", "review"]

        if any(keyword in desc_lower for keyword in high_effort):
            return "3-4 weeks"
        elif any(keyword in desc_lower for keyword in medium_effort):
            return "2-3 weeks"
        elif any(keyword in desc_lower for keyword in low_effort):
            return "1-2 weeks"
        else:
            return "2-3 weeks"

    def _determine_priority(self, index: int, total_items: int) -> str:
        """Determine priority based on position (earlier items tend to be more critical)"""
        priority_ratio = index / max(total_items, 1)

        if priority_ratio < 0.33:
            return "high"
        elif priority_ratio < 0.66:
            return "medium"
        else:
            return "low"
