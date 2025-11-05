"""
Pydantic models for Phase 2: Structured Data Extraction.

Models for:
- Tender information extraction
- Financial data extraction
- Data sheet extraction
- Validation and confidence scoring
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ===== Enums =====

class TenderType(str, Enum):
    """Types of tenders"""
    OPEN = "open"
    LIMITED = "limited"
    EOI = "eoi"
    RATE_CONTRACT = "rateContract"


class TenderStatus(str, Enum):
    """Status of tender"""
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    AWARDED = "awarded"


class Currency(str, Enum):
    """Supported currencies"""
    INR = "INR"


# ===== Money-related Models =====

class MoneyAmount(BaseModel):
    """Represents a monetary amount"""
    amount: float = Field(..., description="Amount in lakhs")
    currency: Currency = Field(default=Currency.INR)
    displayText: str = Field(..., description="Formatted display text, e.g., '₹15.50 Cr'")


# ===== Contact Information =====

class ContactPerson(BaseModel):
    """Contact information for tender issuer"""
    name: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


# ===== Location Information =====

class Coordinates(BaseModel):
    """Geographic coordinates for project"""
    model_config = ConfigDict(populate_by_name=True)

    fromLocation: str = Field(..., description="e.g., 'Km 85+000'")
    toLocation: str = Field(..., description="e.g., 'Km 110+000'")


class ProjectLocation(BaseModel):
    """Geographic location details of the project"""
    state: str
    city: Optional[str] = None
    district: Optional[str] = None
    coordinates: Optional[Coordinates] = None


# ===== TenderInfo Model =====

class TenderInfo(BaseModel):
    """Basic information extracted from tender document"""
    model_config = ConfigDict(from_attributes=True)

    # Identifiers
    referenceNumber: str = Field(..., description="Unique tender reference, e.g., 'PWD/NH-44/2024/ROAD/001'")
    title: str = Field(..., description="Tender title")

    # Organization
    issuingOrganization: str = Field(..., description="Organization issuing the tender")
    department: Optional[str] = None
    contactPerson: Optional[ContactPerson] = None

    # Financial
    estimatedValue: MoneyAmount = Field(..., description="Estimated contract value")

    # Dates
    publishedDate: Optional[str] = None  # ISO 8601
    submissionDeadline: Optional[str] = None  # ISO 8601
    technicalBidOpening: Optional[str] = None  # ISO 8601
    financialBidOpening: Optional[str] = None  # ISO 8601

    # Location
    projectLocation: Optional[ProjectLocation] = None

    # Categories
    category: str = Field(..., description="Tender category, e.g., 'Road Construction'")
    subCategory: Optional[str] = None
    tenderType: TenderType
    status: TenderStatus = Field(default=TenderStatus.ACTIVE)

    # Extraction metadata
    extractionConfidence: float = Field(ge=0.0, le=100.0, description="Confidence score for extraction")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during extraction")


# ===== Financial Information =====

class FinancialRequirements(BaseModel):
    """Financial requirements and breakdown"""
    contractValue: MoneyAmount
    emdAmount: Optional[MoneyAmount] = None
    emdPercentage: Optional[float] = None
    performanceBankGuarantee: Optional[MoneyAmount] = None
    pbgPercentage: Optional[float] = None
    tenderDocumentFee: Optional[MoneyAmount] = None
    processingFee: Optional[MoneyAmount] = None
    totalUpfrontCost: Optional[MoneyAmount] = None

    extractionConfidence: float = Field(ge=0.0, le=100.0)
    warnings: List[str] = Field(default_factory=list)


# ===== Eligibility Information =====

class RequiredSimilarProjects(BaseModel):
    """Requirements for similar projects"""
    count: int
    minimumValue: Optional[MoneyAmount] = None
    timePeriod: Optional[str] = None


class EligibilityHighlights(BaseModel):
    """Key eligibility criteria"""
    minimumExperience: Optional[str] = None
    minimumTurnover: Optional[MoneyAmount] = None
    requiredSimilarProjects: Optional[RequiredSimilarProjects] = None
    specialRelaxations: List[str] = Field(default_factory=list)

    extractionConfidence: float = Field(ge=0.0, le=100.0)
    warnings: List[str] = Field(default_factory=list)


# ===== Key Dates =====

class ProjectDuration(BaseModel):
    """Project duration information"""
    value: int
    unit: str = Field(..., description="days, months, or years")
    displayText: str = Field(..., description="e.g., '24 months'")


class KeyDates(BaseModel):
    """Important dates in the tender process"""
    prebidMeeting: Optional[str] = None
    bidSubmissionDeadline: Optional[str] = None
    technicalEvaluation: Optional[str] = None
    financialBidOpening: Optional[str] = None
    expectedAwardDate: Optional[str] = None
    projectStartDate: Optional[str] = None
    projectDuration: Optional[ProjectDuration] = None

    extractionConfidence: float = Field(ge=0.0, le=100.0)
    warnings: List[str] = Field(default_factory=list)


# ===== OnePagerData =====

class ProjectOverview(BaseModel):
    """High-level project overview"""
    description: str = Field(..., description="100-200 word project description")
    keyHighlights: List[str] = Field(..., description="3-5 key highlights")
    projectScope: Optional[str] = None


class RiskFactors(BaseModel):
    """Risk assessment information"""
    level: str = Field(..., description="low, medium, or high")
    factors: List[str] = Field(default_factory=list)


class CompetitiveAnalysis(BaseModel):
    """Competitive analysis information"""
    estimatedBidders: Optional[str] = None
    complexity: Optional[str] = None  # simple, moderate, complex
    barriers: List[str] = Field(default_factory=list)


class OnePagerData(BaseModel):
    """One-pager summary for quick decision making"""
    model_config = ConfigDict(from_attributes=True)

    projectOverview: Optional[ProjectOverview] = None
    financialRequirements: Optional[FinancialRequirements] = None
    eligibilityHighlights: Optional[EligibilityHighlights] = None
    keyDates: Optional[KeyDates] = None
    riskFactors: Optional[RiskFactors] = None
    competitiveAnalysis: Optional[CompetitiveAnalysis] = None

    extractionConfidence: float = Field(ge=0.0, le=100.0)
    warnings: List[str] = Field(default_factory=list)


# ===== Data Sheet Models =====

class DataSheetRow(BaseModel):
    """A row in the data sheet"""
    key: str = Field(..., description="Field key/name")
    value: Optional[str] = None
    section: Optional[str] = None  # Which section this came from
    confidence: float = Field(ge=0.0, le=100.0)
    dataType: Optional[str] = None  # string, number, currency, date, etc


class DataSheetData(BaseModel):
    """Structured tabular data from tender document"""
    model_config = ConfigDict(from_attributes=True)

    rows: List[DataSheetRow] = Field(default_factory=list)
    totals: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None

    extractionConfidence: float = Field(ge=0.0, le=100.0)
    warnings: List[str] = Field(default_factory=list)


# ===== Validation Result =====

class ExtractionValidationResult(BaseModel):
    """Result of validating extracted structured data"""
    isValid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== Phase 2 Request/Response Models =====

class StructuredExtractionRequest(BaseModel):
    """Request to extract structured data from parsed document"""
    analysis_id: UUID
    raw_text: str = Field(..., description="Raw text from document parser")
    use_llm: bool = Field(default=True, description="Use LLM for extraction vs. keyword-based")


class StructuredExtractionResponse(BaseModel):
    """Response from structured extraction"""
    analysis_id: UUID
    status: str = Field(..., description="success, partial, failed")

    tenderInfo: Optional[TenderInfo] = None
    onePagerData: Optional[OnePagerData] = None
    dataSheet: Optional[DataSheetData] = None

    validationResult: ExtractionValidationResult
    processingDurationMs: int
    extractedAt: datetime = Field(default_factory=datetime.utcnow)
