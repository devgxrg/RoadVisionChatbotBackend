"""
Pydantic models for document extraction and parsing.

Models for:
- Document information and metadata
- Extraction results with quality indicators
- Section-based content structure
- Quality metrics and warnings
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class DocumentMetadata(BaseModel):
    """Metadata about the uploaded document"""
    original_filename: str
    file_size: int  # In bytes
    file_type: str  # e.g., "application/pdf"
    page_count: int
    uploaded_at: datetime


class ExtractedSection(BaseModel):
    """A section extracted from the document"""
    section_number: str = Field(..., description="e.g., '1', '2.1', '3.2.1'")
    title: str
    text: str
    page_numbers: List[int] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=100.0)


class ExtractedTable(BaseModel):
    """A table extracted from the document"""
    table_number: int
    title: Optional[str] = None
    data: Dict[str, Any]  # Raw table data
    page_number: int
    location_on_page: str = Field(default="unknown")  # top, middle, bottom
    confidence: float = Field(ge=0.0, le=100.0)


class ExtractedFigure(BaseModel):
    """A figure/image extracted from the document"""
    figure_number: int
    description: Optional[str] = None
    figure_type: str  # e.g., "diagram", "chart", "image", "table"
    page_number: int
    confidence: float = Field(ge=0.0, le=100.0)


class DocumentExtractionResult(BaseModel):
    """Result of document parsing and extraction"""
    model_config = ConfigDict(from_attributes=True)

    analysis_id: UUID
    metadata: DocumentMetadata

    # Extracted content
    raw_text: str = Field(..., description="Full extracted text from document")
    sections: List[ExtractedSection] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    figures: List[ExtractedFigure] = Field(default_factory=list)

    # Extraction quality
    extraction_quality: float = Field(ge=0.0, le=100.0, description="Overall extraction confidence")
    ocr_required: bool = Field(default=False, description="Was OCR used?")
    ocr_confidence: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    extractable_sections: int = Field(default=0, description="Number of major sections found")

    # Processing metadata
    extraction_started_at: datetime
    extraction_completed_at: datetime
    processing_duration_seconds: float = Field(description="Time taken for extraction")


class QualityWarning(BaseModel):
    """A warning about data quality"""
    field: str = Field(..., description="Which field the warning is about")
    severity: str = Field(..., description="low, medium, high")
    message: str
    recommendation: Optional[str] = None


class QualityRecommendation(BaseModel):
    """A recommendation for improving extraction"""
    priority: str = Field(..., description="low, medium, high, critical")
    suggestion: str
    impact: str = Field(..., description="Brief description of impact if not addressed")


class ExtractionQualityResult(BaseModel):
    """Quality assessment of extraction"""
    model_config = ConfigDict(from_attributes=True)

    analysis_id: UUID

    # Overall metrics
    data_completeness: float = Field(ge=0.0, le=100.0, description="Percentage of expected data extracted")
    overall_confidence: float = Field(ge=0.0, le=100.0, description="Overall confidence in extraction")

    # Section-wise confidence
    tender_info_confidence: float = Field(ge=0.0, le=100.0)
    financial_confidence: float = Field(ge=0.0, le=100.0)
    scope_confidence: float = Field(ge=0.0, le=100.0)
    rfp_sections_confidence: float = Field(ge=0.0, le=100.0)
    eligibility_confidence: float = Field(ge=0.0, le=100.0)

    # Quality issues
    warnings: List[QualityWarning] = Field(default_factory=list)
    recommendations: List[QualityRecommendation] = Field(default_factory=list)

    # Content summary
    sections_extracted: int
    tables_extracted: int
    figures_extracted: int
    annexures_identified: int

    created_at: datetime
    updated_at: datetime


class DocumentParserRequest(BaseModel):
    """Request to parse a tender document"""
    analysis_id: UUID
    file_path: str = Field(..., description="Path to the PDF file")
    file_size: int = Field(..., description="File size in bytes")


class DocumentParserResponse(BaseModel):
    """Response from document parser"""
    analysis_id: UUID
    status: str = Field(..., description="success, partial, failed")
    extraction_result: Optional[DocumentExtractionResult] = None
    quality_result: Optional[ExtractionQualityResult] = None
    error: Optional[Dict[str, str]] = None
    processing_duration_ms: int
