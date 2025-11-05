"""
RFP Extraction Service

Extracts and analyzes RFP (Request for Proposal) sections from tender documents.
"""
import os
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.tenderiq.db.tenderiq_repository import TenderIQRepository
from app.modules.tenderiq.services.document_parser import DocumentParser
from app.modules.tenderiq.services.rfp_section_analyzer import RFPSectionAnalyzer
from app.modules.tenderiq.models.pydantic_models import (
    RFPAnalysisResponse,
    RFPSectionResponse,
    RFPSectionSummaryResponse,
    RFPSectionComplianceResponse,
)


class RFPExtractionService:
    """Service for extracting and analyzing RFP sections"""

    def __init__(self):
        pass

    async def extract_rfp_sections(
        self,
        db: Session,
        tender_id: UUID,
        section_number: Optional[str] = None,
        include_compliance: bool = False,
    ) -> RFPAnalysisResponse:
        """
        Perform on-demand RFP section extraction from tender documents.
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

        # 3. Analyze RFP sections
        rfp_analyzer = RFPSectionAnalyzer()
        rfp_data = await rfp_analyzer.analyze_rfp_sections(db, uuid4(), raw_text)

        # 4. Map result to response model
        section_responses = []
        criticality_counts = {"high": 0, "medium": 0, "low": 0}

        for section_data in rfp_data.get("sections", []):
            if section_number and section_data.get("sectionNumber") != section_number:
                continue

            complexity = self.assess_section_complexity(section_data.get("content", ""))
            criticality_counts[complexity] += 1
            
            compliance = None
            if include_compliance:
                compliance = RFPSectionComplianceResponse(status="requires-review", issues=[])

            section_responses.append(
                RFPSectionResponse(
                    id=uuid4(),
                    number=section_data.get("sectionNumber", "N/A"),
                    title=section_data.get("title", "Untitled Section"),
                    description=section_data.get("content", ""),
                    key_requirements=section_data.get("requirements", []),
                    compliance=compliance,
                    estimated_complexity=complexity,
                    related_sections=[],
                    document_references=[],
                )
            )

        return RFPAnalysisResponse(
            tender_id=tender_id,
            total_sections=len(section_responses),
            sections=section_responses,
            summary=RFPSectionSummaryResponse(
                total_requirements=rfp_data.get("total_requirements", 0),
                criticality=criticality_counts,
            ),
        )

    def identify_requirements(self, section_text: str) -> List[str]:
        """
        Extract key requirements from an RFP section.

        Uses sentence-based parsing. TODO: Upgrade to LLM-based extraction.

        Args:
            section_text: Text of the RFP section

        Returns:
            List of identified requirements
        """
        if not section_text:
            return []

        requirements = []

        # Split by common requirement keywords
        requirement_keywords = ["must", "shall", "required", "should", "need", "provide"]
        sentences = section_text.split(".")

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if any(keyword in sentence_clean.lower() for keyword in requirement_keywords):
                if len(sentence_clean) > 10:  # Filter out very short strings
                    requirements.append(sentence_clean)

        # Remove duplicates while preserving order
        seen = set()
        unique_requirements = []
        for req in requirements:
            if req not in seen:
                seen.add(req)
                unique_requirements.append(req)

        return unique_requirements[:10]  # Return top 10 requirements

    def assess_section_complexity(self, section_text: str) -> str:
        """
        Estimate complexity of an RFP section (low/medium/high).

        Uses heuristics based on section length and keywords.

        Args:
            section_text: Text of the RFP section

        Returns:
            Complexity level: "low", "medium", or "high"
        """
        if not section_text:
            return "medium"

        text_lower = section_text.lower()

        # High complexity indicators
        high_complexity_keywords = [
            "architecture", "implementation", "security", "performance",
            "integration", "compliance", "regulation", "technical",
            "infrastructure", "enterprise", "scalability", "recovery"
        ]

        # Low complexity indicators
        low_complexity_keywords = [
            "basic", "simple", "standard", "general", "eligibility",
            "registration", "name", "address", "contact"
        ]

        high_score = sum(text_lower.count(keyword) for keyword in high_complexity_keywords)
        low_score = sum(text_lower.count(keyword) for keyword in low_complexity_keywords)
        word_count = len(section_text.split())

        # Calculate complexity
        if high_score > low_score and word_count > 200:
            return "high"
        elif low_score > high_score or word_count < 100:
            return "low"
        else:
            return "medium"

    def identify_missing_documents(
        self,
        sections: List[dict],
        provided_documents: List[str]
    ) -> List[str]:
        """
        Identify documents referenced in RFP but not provided.

        Args:
            sections: RFP sections with requirements
            provided_documents: List of document names provided

        Returns:
            List of missing document names
        """
        if not sections:
            return []

        document_keywords = [
            "document", "certificate", "letter", "report", "statement",
            "plan", "proposal", "specification", "design", "drawing"
        ]

        mentioned_documents = set()
        provided_lower = [doc.lower() for doc in provided_documents]

        for section in sections:
            description = section.get("description", "").lower()
            requirements = [req.lower() for req in section.get("requirements", [])]

            # Search for document references
            all_text = " ".join([description] + requirements)

            for keyword in document_keywords:
                if keyword in all_text:
                    # Extract document type (e.g., "Technical Document", "Audit Report")
                    words = all_text.split()
                    for i, word in enumerate(words):
                        if keyword in word.lower() and i > 0:
                            doc_name = " ".join(words[max(0, i-2):i+1])
                            mentioned_documents.add(doc_name)

        # Find missing documents
        missing = []
        for doc in mentioned_documents:
            if not any(doc.lower() in prov.lower() or prov.lower() in doc.lower()
                      for prov in provided_lower):
                missing.append(doc)

        return list(missing)[:5]  # Return top 5 missing documents

    # ==================== Helper Methods ====================

    def _find_related_sections(self, section_number: str) -> List[str]:
        """Find related section numbers"""
        # In a real implementation, would use semantic analysis
        # For now, return sections with adjacent numbers
        try:
            num = float(section_number)
            related = [
                str(num + 0.1),
                str(num + 1.0),
            ]
            return [r for r in related if r != section_number]
        except ValueError:
            return []
