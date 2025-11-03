# TenderIQ Date Filtering - Implementation Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend Application                        │
│  (React/Vue - populates date selector, shows filtered results)       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ HTTP Requests
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend Layer                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ API Endpoints (tenderiq/endpoints/tenders.py)               │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ GET /api/v1/tenderiq/dates                                  │  │
│  │ GET /api/v1/tenderiq/tenders?date_range=...&category=...   │  │
│  │ GET /api/v1/tenderiq/dailytenders (existing)                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                         │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Service Layer (tenderiq/services/tender_filter_service.py)  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ TenderFilterService                                         │  │
│  │  ├─ get_available_dates()                                  │  │
│  │  ├─ get_tenders_by_date_range(days, filters)              │  │
│  │  ├─ get_tenders_by_specific_date(date, filters)           │  │
│  │  └─ get_all_tenders(filters)                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                         │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Repository Layer (scraper/db/repository.py - Extended)      │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ ScraperRepository                                           │  │
│  │  ├─ get_latest_scrape_run() [EXISTING]                    │  │
│  │  ├─ get_scrape_runs_by_date_range(days) [NEW]             │  │
│  │  ├─ get_tenders_by_scrape_run(id, filters) [NEW]          │  │
│  │  ├─ get_available_scrape_runs() [NEW]                     │  │
│  │  └─ get_tenders_by_specific_date(date, filters) [NEW]     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                         │
│                           ↓                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Pydantic Models (tenderiq/models/pydantic_models.py)        │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ TenderResponse                                              │  │
│  │ ScrapeDateInfo                                              │  │
│  │ AvailableDatesResponse                                      │  │
│  │ FilteredTendersResponse                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                         │
│                           ↓                                         │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           │ SQLAlchemy ORM
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database Layer                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐         ┌──────────────────────┐          │
│  │   ScrapeRun Table    │         │ ScrapedTender Table  │          │
│  ├──────────────────────┤         ├──────────────────────┤          │
│  │ id (UUID) [PK]      │         │ id (UUID) [PK]       │          │
│  │ run_at (DateTime) [INDEX]     │ tender_id_str        │          │
│  │ date_str (String)   │         │ tender_name          │          │
│  │ name                │         │ city                 │          │
│  │ company             │         │ value                │          │
│  │ created_at          │         │ due_date (String)    │          │
│  │ etc...              │         │ scrape_run_id [FK]   │──┐       │
│  └──────────────────────┘         │ query_id [FK]        │  │       │
│           ▲                       │ etc...               │  │       │
│           │                       └──────────────────────┘  │       │
│           └───────────────────────────────────────────────── │       │
│                                                              │       │
│  ┌──────────────────────┐         ┌──────────────────────┐  │       │
│  │ScrapedTenderQuery Tbl│         │ ScrapedTenderFile Tbl│  │       │
│  ├──────────────────────┤         ├──────────────────────┤  │       │
│  │ id (UUID) [PK]      │         │ id (UUID)            │  │       │
│  │ query_name          │         │ file_name            │  │       │
│  │ scrape_run_id [FK] ─┤         │ tender_id [FK] ──────┼──┘       │
│  │ etc...              │         │ etc...               │          │
│  └──────────────────────┘         └──────────────────────┘          │
│                                                                      │
│  Indexes:                                                           │
│  ├─ ScrapeRun(run_at) - for date range queries                     │
│  ├─ ScrapeRun(created_at) - for ordering                           │
│  ├─ ScrapedTender(scrape_run_id) - for lookups                     │
│  └─ ScrapedTender(tender_id_str) - already exists                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Structure & Changes

```
app/modules/tenderiq/
├── models/
│   └── pydantic_models.py
│       ├── TenderResponse (NEW)
│       ├── ScrapeDateInfo (NEW)
│       ├── AvailableDatesResponse (NEW)
│       ├── FilteredTendersResponse (NEW)
│       └── DailyTendersResponse (EXISTING)
│
├── services/
│   ├── tender_service.py (EXISTING)
│   └── tender_filter_service.py (NEW)
│       └── TenderFilterService class
│
└── endpoints/
    └── tenders.py (EXTENDED)
        ├── get_daily_tenders() (EXISTING)
        ├── get_available_dates() (NEW)
        └── get_filtered_tenders() (NEW)

app/modules/scraper/db/
└── repository.py (EXTENDED)
    ├── get_latest_scrape_run() (EXISTING)
    ├── get_scrape_runs_by_date_range() (NEW)
    ├── get_tenders_by_scrape_run() (NEW)
    ├── get_available_scrape_runs() (NEW)
    └── get_tenders_by_specific_date() (NEW)

tests/unit/
└── test_tenderiq_date_filtering.py (NEW)
    ├── TestScraperRepository
    ├── TestTenderFilterService
    └── TestTenderEndpoints
```

---

## Data Query Flows

### Flow 1: Get Available Dates
```
Frontend Request
    ↓
GET /api/v1/tenderiq/dates
    ↓
Endpoint: get_available_dates()
    ↓
Service: get_available_dates()
    ↓
Repository: get_available_scrape_runs()
    ↓
SQL Query:
  SELECT id, run_at, date_str, COUNT(tenders)
  FROM scrape_run
  LEFT JOIN scraped_tender_query ON ...
  LEFT JOIN scraped_tender ON ...
  GROUP BY scrape_run.id
  ORDER BY run_at DESC
    ↓
Return: AvailableDatesResponse
  {
    "dates": [
      {
        "date": "2024-11-03",
        "date_str": "November 3, 2024",
        "run_at": "2024-11-03T10:30:00Z",
        "tender_count": 45,
        "is_latest": true
      },
      ...
    ]
  }
```

### Flow 2: Get Tenders by Date Range
```
Frontend Request
    ↓
GET /api/v1/tenderiq/tenders?date_range=last_5_days&category=Civil
    ↓
Endpoint: get_filtered_tenders(date_range, category, ...)
    ↓
Service: get_tenders_by_date_range(5, filters)
    ↓
Calculate: cutoff_date = now() - 5 days
    ↓
Repository: get_scrape_runs_by_date_range(5)
    ↓
SQL Query:
  SELECT *
  FROM scrape_run
  WHERE run_at >= cutoff_date
  ORDER BY run_at DESC
    ↓
For each scrape_run:
  Repository: get_tenders_by_scrape_run(id, category)
    ↓
    SQL Query:
      SELECT st.*
      FROM scraped_tender st
      JOIN scraped_tender_query stq ON st.query_id = stq.id
      WHERE stq.scrape_run_id = ?
      AND st.query_name = ? (if category filter)
      AND st.city = ? (if location filter)
      AND st.value >= ? AND st.value <= ? (if value filter)
    ↓
Aggregate results
    ↓
Return: FilteredTendersResponse
  {
    "tenders": [ {...}, {...}, ... ],
    "total_count": 127,
    "filtered_by": {
      "date_range": "last_5_days",
      "category": "Civil"
    },
    "available_dates": ["2024-11-03", "2024-11-02", ...]
  }
```

### Flow 3: Get Tenders by Specific Date
```
Frontend Request
    ↓
GET /api/v1/tenderiq/tenders?date=2024-11-03
    ↓
Service: get_tenders_by_specific_date("2024-11-03", filters)
    ↓
Parse date: "2024-11-03" → datetime(2024, 11, 3)
    ↓
Repository: get_scrape_runs_by_date_range() with specific date
    ↓
SQL Query:
  SELECT *
  FROM scrape_run
  WHERE DATE(run_at) = '2024-11-03'
    ↓
Get tenders from matching scrape runs
    ↓
Return: FilteredTendersResponse
```

---

## Request/Response Examples

### Endpoint 1: GET /api/v1/tenderiq/dates

**Response:**
```json
{
  "dates": [
    {
      "date": "2024-11-03",
      "date_str": "November 3, 2024",
      "run_at": "2024-11-03T10:30:00Z",
      "tender_count": 45,
      "is_latest": true
    },
    {
      "date": "2024-11-02",
      "date_str": "November 2, 2024",
      "run_at": "2024-11-02T09:15:00Z",
      "tender_count": 38,
      "is_latest": false
    },
    {
      "date": "2024-11-01",
      "date_str": "November 1, 2024",
      "run_at": "2024-11-01T10:45:00Z",
      "tender_count": 42,
      "is_latest": false
    }
  ]
}
```

### Endpoint 2: GET /api/v1/tenderiq/tenders

**Query Parameters:**
```
?date_range=last_5_days
&category=Civil
&location=Mumbai
&min_value=100
&max_value=500
```

**Response:**
```json
{
  "tenders": [
    {
      "tender_id_str": "TEN-2024-001",
      "tender_name": "Construction of Multi-Story Building",
      "tender_url": "https://...",
      "city": "Mumbai",
      "value": "250 Crore",
      "due_date": "2024-11-15",
      "summary": "..."
    },
    {
      "tender_id_str": "TEN-2024-002",
      "tender_name": "Road Construction Project",
      "tender_url": "https://...",
      "city": "Mumbai",
      "value": "180 Crore",
      "due_date": "2024-11-12",
      "summary": "..."
    }
  ],
  "total_count": 12,
  "filtered_by": {
    "date_range": "last_5_days",
    "category": "Civil",
    "location": "Mumbai",
    "min_value": 100,
    "max_value": 500
  },
  "available_dates": [
    "2024-11-03",
    "2024-11-02",
    "2024-11-01",
    "2024-10-31",
    "2024-10-30"
  ]
}
```

---

## Class & Method Signatures

### Repository Layer

```python
class ScraperRepository:
    def __init__(self, db: Session):
        self.db = db

    # EXISTING
    def get_latest_scrape_run(self) -> Optional[ScrapeRun]:
        """Get most recent scrape run with all relationships eager loaded"""

    # NEW METHODS
    def get_scrape_runs_by_date_range(
        self,
        days: Optional[int] = None
    ) -> List[ScrapeRun]:
        """
        Get scrape runs from last N days.
        Args:
            days: Number of days back (None = all)
        Returns:
            List of ScrapeRun objects with relationships loaded
        """

    def get_available_scrape_runs(self) -> List[ScrapeRun]:
        """
        Get all distinct scrape runs ordered newest first.
        Returns:
            List of ScrapeRun with eager-loaded relationships
        """

    def get_tenders_by_scrape_run(
        self,
        scrape_run_id: UUID,
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> List[ScrapedTender]:
        """
        Get all tenders from specific scrape run with optional filters.
        """

    def get_tenders_by_specific_date(
        self,
        date: str,  # "YYYY-MM-DD"
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> List[ScrapedTender]:
        """
        Get all tenders from specific date.
        """
```

### Service Layer

```python
class TenderFilterService:
    def get_available_dates(
        self,
        db: Session
    ) -> AvailableDatesResponse:
        """Get all available scrape dates with tender counts"""

    def get_tenders_by_date_range(
        self,
        db: Session,
        date_range: str,  # "last_1_day", "last_5_days", etc.
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> FilteredTendersResponse:
        """Get tenders from relative date range"""

    def get_tenders_by_specific_date(
        self,
        db: Session,
        date: str,  # "YYYY-MM-DD"
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> FilteredTendersResponse:
        """Get tenders from specific date"""

    def get_all_tenders(
        self,
        db: Session,
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> FilteredTendersResponse:
        """Get all historical tenders"""
```

### Endpoint Layer

```python
@router.get("/dates", response_model=AvailableDatesResponse)
def get_available_dates(db: Session = Depends(get_db_session)):
    """Get available scrape dates"""

@router.get("/tenders", response_model=FilteredTendersResponse)
def get_filtered_tenders(
    db: Session = Depends(get_db_session),
    date: Optional[str] = Query(None),
    date_range: Optional[str] = Query(None),
    include_all_dates: bool = Query(False),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
):
    """Get filtered tenders"""
```

---

## SQL Query Optimization

### Key Indexes to Add/Verify

```sql
-- Verify existing
CREATE INDEX IF NOT EXISTS idx_scraped_tender_tender_id_str
ON scraped_tender(tender_id_str);

-- New indexes needed
CREATE INDEX IF NOT EXISTS idx_scrape_run_run_at
ON scrape_run(run_at DESC);

CREATE INDEX IF NOT EXISTS idx_scrape_run_date_str
ON scrape_run(date_str);

CREATE INDEX IF NOT EXISTS idx_scraped_tender_scrape_run_id
ON scraped_tender(scrape_run_id);

CREATE INDEX IF NOT EXISTS idx_scraped_tender_query_name
ON scraped_tender(query_name);

CREATE INDEX IF NOT EXISTS idx_scraped_tender_city
ON scraped_tender(city);
```

### Query Performance Estimates

```
Scenario: Get tenders from last 5 days with category filter
Tenders per day: ~40-50
Total: ~200-250 tenders

Estimated execution time:
├─ Query ScrapeRun (5 rows): ~1ms
├─ Join to queries: ~2ms
├─ Filter by category: ~3ms
└─ Format response: ~5ms
Total: ~11ms (without caching)
```

---

## Error Handling

### Invalid Date Format
```python
# If user sends: date=11-03-2024 (invalid format)
# Return 400 Bad Request
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

### Invalid Date Range
```python
# If user sends: date_range=last_100_days (invalid option)
# Return 400 Bad Request
{
  "detail": "Invalid date_range. Must be one of: last_1_day, last_5_days, last_7_days, last_30_days"
}
```

### No Data Found
```python
# If no tenders match filters
# Return 200 OK with empty results
{
  "tenders": [],
  "total_count": 0,
  "filtered_by": {...},
  "available_dates": [...]
}
```

---

## Caching Strategy (Optional for Phase 6)

```python
from functools import lru_cache
from datetime import timedelta

class TenderFilterService:
    @cache(ttl=timedelta(hours=1))
    def get_available_dates(self, db: Session):
        """Cache dates for 1 hour since new scrapes happen daily"""
        ...

    # Don't cache tenders queries (too many variations)
    def get_tenders_by_date_range(self, ...):
        """No caching - always fresh data"""
        ...
```

---

## Testing Strategy

### Unit Tests
```python
# test_tenderiq_date_filtering.py

class TestScraperRepository:
    @pytest.fixture
    def mock_scrape_runs(self):
        # Create 10 fake scrape runs over past 10 days

    def test_get_scrape_runs_by_date_range_last_5_days(self, mock_scrape_runs):
        result = repo.get_scrape_runs_by_date_range(5)
        assert len(result) == 5

    def test_get_tenders_by_specific_date(self, mock_scrape_runs):
        result = repo.get_tenders_by_specific_date("2024-11-03")
        assert all(t.scrape_run.date_str == "November 3, 2024")

class TestTenderFilterService:
    def test_get_available_dates(self):
        result = service.get_available_dates(db)
        assert len(result.dates) > 0
        assert result.dates[0].is_latest == True

class TestTenderEndpoints:
    def test_get_dates_endpoint_returns_200(self):
        response = client.get("/api/v1/tenderiq/dates")
        assert response.status_code == 200

    def test_get_tenders_with_date_range_filter(self):
        response = client.get("/api/v1/tenderiq/tenders?date_range=last_5_days")
        assert response.status_code == 200
        assert "tenders" in response.json()
```

---

## Summary

**Total files to create/modify**: 6-8
**Total lines of code**: 800-1200
**Complexity**: Medium (straightforward SQLAlchemy + FastAPI)
**Risk**: Low (no database schema changes, new endpoints only)

**Ready to implement?** ✅ Yes
