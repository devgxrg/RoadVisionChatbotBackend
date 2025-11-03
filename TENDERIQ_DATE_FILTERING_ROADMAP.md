# TenderIQ Date Filtering Implementation Roadmap

**Status**: Feasible ✅
**Complexity**: Medium
**Estimated Duration**: 2-3 weeks
**Frontend Team Request**: [TENDERIQ_API_SUGGESTIONS.json](./ceigall-suite/TENDERIQ_API_SUGGESTIONS.json)

---

## 📋 Executive Summary

The frontend team has requested the ability to filter tenders by date. This roadmap outlines a complete implementation plan to add:
1. **Date range filtering** (last 1, 5, 7, 30 days)
2. **Specific date filtering** (select a single date)
3. **Historical data access** (view all available tenders)
4. **Date availability endpoint** (populate date selectors)
5. **Additional filters** (category, location, value range)

**Verdict**: This is **fully feasible** with the current database structure. No major architectural changes needed.

---

## 🔍 Current State Analysis

### Existing Data Structure ✅

**Good News:**
- ✅ `ScrapeRun` table already tracks `run_at` (DateTime) and `date_str` (String)
- ✅ Tenders are linked to scrape runs via `ScrapedTenderQuery.scrape_run_id`
- ✅ All necessary historical data is already stored
- ✅ Database can already query by date ranges

**Challenges:**
- ⚠️ Date fields in ScrapedTender are stored as **Strings**, not DateTime (e.g., `due_date`, `publish_date`)
  - This is acceptable for filtering on **scrape date**, not individual tender dates
  - Would need conversion for filtering by tender deadline dates

**Current API:**
```
GET /api/v1/tenderiq/dailytenders → Returns only latest scrape date
```

### Data Flow
```
ScrapeRun (run_at, date_str)
    ↓ (one-to-many)
ScrapedTenderQuery (query_name, scrape_run_id)
    ↓ (one-to-many)
ScrapedTender (tender details)
```

---

## 🎯 Implementation Roadmap

### Phase 1: Database Query Layer Enhancement (3-4 days)

#### 1.1 Extend ScraperRepository with new query methods

**File**: `app/modules/scraper/db/repository.py`

```python
def get_scrape_runs_by_date_range(
    self,
    days: Optional[int] = None
) -> List[ScrapeRun]:
    """
    Get scrape runs from last N days.
    days=1 → last 1 day
    days=5 → last 5 days
    days=None → all historical runs
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
    Get all tenders from a specific scrape run with optional filters.
    """

def get_available_scrape_runs(self) -> List[ScrapeRun]:
    """
    Get all distinct scrape runs ordered by date (newest first).
    Includes count of tenders per run.
    """

def get_tenders_by_specific_date(
    self,
    date: str,  # YYYY-MM-DD format
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> List[ScrapedTender]:
    """
    Get all tenders from a specific date.
    """
```

**Tasks:**
- [ ] Add `get_scrape_runs_by_date_range()` method
- [ ] Add `get_tenders_by_scrape_run()` method with category/location/value filtering
- [ ] Add `get_available_scrape_runs()` method (for dates endpoint)
- [ ] Add `get_tenders_by_specific_date()` method
- [ ] Add database indexes on `ScrapeRun.run_at` (if not already present)
- [ ] Write unit tests for each method

---

### Phase 2: Pydantic Models & Response Schemas (2-3 days)

#### 2.1 Create new Pydantic models

**File**: `app/modules/tenderiq/models/pydantic_models.py`

```python
class TenderResponse(BaseModel):
    """Single tender for API response"""
    tender_id_str: str
    tender_name: str
    tender_url: str
    city: str
    value: str
    due_date: str
    # Additional fields as needed
    # Remove sensitive fields

class ScrapeDateInfo(BaseModel):
    """Information about a specific scrape date"""
    date: str  # YYYY-MM-DD
    date_str: str  # "November 3, 2024"
    run_at: datetime  # ISO format
    tender_count: int
    is_latest: bool

class AvailableDatesResponse(BaseModel):
    """Response for /api/v1/tenderiq/dates endpoint"""
    dates: List[ScrapeDateInfo]

class FilteredTendersResponse(BaseModel):
    """Response for /api/v1/tenderiq/tenders endpoint"""
    tenders: List[TenderResponse]
    total_count: int
    filtered_by: dict  # What filters were applied
    available_dates: List[str]  # All available dates for UI
```

**Tasks:**
- [ ] Create `TenderResponse` model
- [ ] Create `ScrapeDateInfo` model
- [ ] Create `AvailableDatesResponse` model
- [ ] Create `FilteredTendersResponse` model
- [ ] Add validation for date formats (YYYY-MM-DD)
- [ ] Add example values for API documentation

---

### Phase 3: Service Layer (2-3 days)

#### 3.1 Create TenderFilterService

**File**: `app/modules/tenderiq/services/tender_filter_service.py` (new)

```python
class TenderFilterService:
    """Service for filtering and retrieving tenders by date and other criteria"""

    def get_available_dates(self, db: Session) -> AvailableDatesResponse:
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
        """Get tenders from a relative date range"""

    def get_tenders_by_specific_date(
        self,
        db: Session,
        date: str,  # YYYY-MM-DD
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> FilteredTendersResponse:
        """Get tenders from a specific date"""

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

**Logic:**
- Parse date ranges (last_1_day → calculate date 1 day ago)
- Call repository methods with appropriate filters
- Format response with metadata
- Handle edge cases (no data found, invalid dates)

**Tasks:**
- [ ] Create `TenderFilterService` class
- [ ] Implement `get_available_dates()` method
- [ ] Implement `get_tenders_by_date_range()` method
- [ ] Implement `get_tenders_by_specific_date()` method
- [ ] Implement `get_all_tenders()` method
- [ ] Add logging for debugging
- [ ] Add caching decorator for dates endpoint (optional but recommended)

---

### Phase 4: API Endpoints (2-3 days)

#### 4.1 Add date filtering endpoints

**File**: `app/modules/tenderiq/endpoints/tenders.py`

```python
@router.get(
    "/dates",
    response_model=AvailableDatesResponse,
    tags=["TenderIQ"],
    summary="Get available scrape dates"
)
def get_available_dates(db: Session = Depends(get_db_session)):
    """
    Returns all available scrape dates with tender counts.
    Frontend uses this to populate date selector dropdown.
    """

@router.get(
    "/tenders",
    response_model=FilteredTendersResponse,
    tags=["TenderIQ"],
    summary="Get tenders with date and other filters"
)
def get_filtered_tenders(
    db: Session = Depends(get_db_session),
    date: Optional[str] = Query(None, description="Specific date (YYYY-MM-DD)"),
    date_range: Optional[str] = Query(None, description="last_1_day, last_5_days, etc."),
    include_all_dates: bool = Query(False),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
):
    """
    Retrieves tenders with optional filtering by:
    - Specific date
    - Date range (last N days)
    - Category, location, value range

    Priority: include_all_dates > date > date_range
    """
```

**Tasks:**
- [ ] Create `GET /api/v1/tenderiq/dates` endpoint
- [ ] Create `GET /api/v1/tenderiq/tenders` endpoint
- [ ] Add query parameter validation
- [ ] Add error handling (400 Bad Request for invalid filters)
- [ ] Add response examples in docstrings
- [ ] Test endpoint with curl/Postman

---

### Phase 5: Testing (2-3 days)

#### 5.1 Unit Tests

**File**: `tests/unit/test_tenderiq_date_filtering.py` (new)

```python
class TestTenderRepository:
    def test_get_scrape_runs_by_date_range_last_5_days()
    def test_get_scrape_runs_by_date_range_all()
    def test_get_tenders_by_specific_date()
    def test_get_available_scrape_runs()

class TestTenderFilterService:
    def test_get_available_dates()
    def test_get_tenders_by_date_range()
    def test_get_tenders_with_category_filter()
    def test_get_tenders_with_value_filter()
    def test_invalid_date_format()

class TestTenderEndpoints:
    def test_get_dates_endpoint()
    def test_get_tenders_endpoint_by_date()
    def test_get_tenders_endpoint_by_range()
    def test_get_tenders_endpoint_all_dates()
    def test_filter_parameter_validation()
```

**Tasks:**
- [ ] Write repository tests (mocked database)
- [ ] Write service tests (mocked repository)
- [ ] Write endpoint tests (mocked service or integration tests)
- [ ] Test filter combinations (date + category + value)
- [ ] Test edge cases (no data, invalid dates)
- [ ] Achieve 80%+ code coverage

#### 5.2 Integration Tests

- [ ] Create test database with sample data from multiple dates
- [ ] Test actual database queries with real data
- [ ] Test pagination if implemented (Phase 6)
- [ ] Load testing for large result sets

---

### Phase 6: Optional Enhancements (1-2 weeks)

#### 6.1 Pagination

Add pagination for large result sets:
```python
@router.get("/tenders")
def get_filtered_tenders(
    ...,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
```

#### 6.2 Sorting

Add sorting options:
```python
sort_by: Optional[str] = Query("date", enum=["date", "value", "name"])
sort_order: str = Query("desc", enum=["asc", "desc"])
```

#### 6.3 Caching

Add caching for dates endpoint:
```python
from functools import lru_cache

@lru_cache(maxsize=1, ttl=3600)  # Cache for 1 hour
def get_available_dates():
    ...
```

#### 6.4 Advanced Filters

- Filter by tender status (open, closed, etc.)
- Filter by minimum/maximum number of days until deadline
- Search by tender name (full text search)

#### 6.5 Performance Optimization

- Add database indexes on frequently filtered columns
- Consider materialized views for complex queries
- Profile query performance

---

## 📊 Data Flow Diagram

```
Frontend Request
    ↓
GET /api/v1/tenderiq/dates  →  TenderFilterService.get_available_dates()
                                    ↓
                                ScraperRepository.get_available_scrape_runs()
                                    ↓
                                Query ScrapeRun table (ordered by run_at DESC)
                                    ↓
                                Format: List[ScrapeDateInfo]
                                    ↓
                                Return: AvailableDatesResponse

GET /api/v1/tenderiq/tenders?date_range=last_5_days
                            → TenderFilterService.get_tenders_by_date_range()
                                    ↓
                                Calculate date 5 days ago
                                    ↓
                                ScraperRepository.get_scrape_runs_by_date_range(5)
                                    ↓
                                For each scrape_run:
                                  - Get tenders
                                  - Apply category/location/value filters
                                    ↓
                                Format: List[TenderResponse]
                                    ↓
                                Return: FilteredTendersResponse
```

---

## 🗄️ Database Considerations

### Current Indexes
- `ScrapeRun.run_at` - **May need to add if not present**
- `ScrapedTender.tender_id_str` - Already exists

### Queries We'll Run
1. Get scrape runs between date range: `O(log n)` with index on `run_at`
2. Get tenders for scrape_run: `O(k)` where k = tenders in that run
3. Filter by category/location: `O(k log k)` in memory after query

### Optimization Opportunities
- Add composite index: `(run_at, created_at)`
- Cache dates list (changes only when new scrape completes)
- Consider denormalization if queries become slow

---

## 🔐 Security & Auth

### Current State
- All endpoints use `Depends(get_db_session)`
- Auth not explicitly shown in current tenders endpoint

### Recommended
- Use existing auth middleware (if available)
- Frontend team confirms: endpoints should use same auth as existing `/dailytenders`
- No additional security needed for date filtering

---

## 🧪 Testing Strategy

### Test Data Setup
```python
# Create test fixture with multiple scrape runs
@pytest.fixture
def scrape_runs_with_dates():
    today = datetime.now()
    return [
        ScrapeRun(run_at=today - timedelta(days=i), ...)
        for i in range(10)
    ]
```

### Test Cases Priority
1. **Critical**: Date range filtering works
2. **Critical**: Specific date filtering works
3. **High**: Filter combinations work (date + category)
4. **High**: All filters return correct count
5. **Medium**: Edge cases (no data, invalid dates)
6. **Medium**: Response format matches schema

---

## 📝 Implementation Checklist

### Week 1: Database & Models
- [ ] Add repository query methods
- [ ] Add database index on `ScrapeRun.run_at`
- [ ] Create Pydantic models
- [ ] Write repository tests

### Week 2: Service & Endpoints
- [ ] Create filter service
- [ ] Add endpoints (`/dates` and `/tenders`)
- [ ] Parameter validation
- [ ] Service tests

### Week 3: Testing & Documentation
- [ ] Integration tests
- [ ] Manual testing with Postman/curl
- [ ] Update API documentation
- [ ] Frontend integration support
- [ ] Performance testing

### Optional Enhancements
- [ ] Pagination support
- [ ] Caching layer
- [ ] Advanced filters
- [ ] Performance optimization

---

## 🚀 Frontend Integration Guide

### Step 1: Populate Date Selector
```javascript
// Frontend code (example)
async function loadAvailableDates() {
    const response = await fetch('/api/v1/tenderiq/dates');
    const data = await response.json();

    // Populate dropdown with data.dates
    // Show "Last 1 day", "Last 5 days" as options
    // Show specific dates from data.available_dates
}
```

### Step 2: Fetch Filtered Tenders
```javascript
async function fetchTenders(dateRange, category, location) {
    const params = new URLSearchParams({
        date_range: dateRange,  // "last_5_days"
        category: category,
        location: location,
    });

    const response = await fetch(`/api/v1/tenderiq/tenders?${params}`);
    const data = await response.json();

    // Display data.tenders in table
    // Show data.filtered_by as active filters
}
```

---

## ⚠️ Known Challenges & Solutions

### Challenge 1: Date String Parsing
**Issue**: Tender `due_date`, `publish_date` are stored as Strings
**Impact**: Can't filter by tender deadline, only by scrape date
**Solution**: Current request only filters by scrape date, which is fine
**Future**: Could parse dates in migration if needed (Phase 6)

### Challenge 2: Large Historical Data
**Issue**: If many scrape runs exist, query could be slow
**Impact**: Performance degradation with `include_all_dates=true`
**Solution**:
- Add pagination (Phase 6)
- Add database indexes
- Implement caching for dates

### Challenge 3: Filter Combinations
**Issue**: Multiple filters (date + category + location) could be complex
**Impact**: Need to carefully structure SQL queries
**Solution**:
- Build queries dynamically with SQLAlchemy
- Use ORM efficiently
- Write comprehensive tests

### Challenge 4: Frontend Expectations
**Issue**: Frontend may expect different response format
**Impact**: API mismatch
**Solution**:
- Confirm schema matches `TENDERIQ_API_SUGGESTIONS.json`
- Early communication with frontend
- Version API if schema changes

---

## 📈 Success Metrics

✅ **Completion Criteria**:
1. All endpoints return correct data
2. Filters work individually and in combination
3. Response format matches spec
4. All tests pass (>80% coverage)
5. Frontend can populate date selector
6. Frontend can fetch filtered results
7. Performance acceptable (<2s for typical queries)
8. Documentation complete

---

## 🔄 Related Considerations

### Email Listener Integration
- Email listener already scrapes tenders (from previous Phase)
- New scrape runs create historical data automatically
- No changes needed to scraper for this feature

### AskAI RAG Integration
- RAG uses Weaviate for semantic search
- Could be integrated with date filtering later
- Not needed for Phase 1

### DMS Integration
- Some tenders link to DMS folders (`dms_folder_id`)
- Can be preserved in responses
- No changes needed

---

## 📞 Communication Checklist

Before starting implementation:
- [ ] Confirm API endpoint paths with frontend
- [ ] Confirm response schema format
- [ ] Confirm required vs optional filters
- [ ] Confirm date format (confirm YYYY-MM-DD)
- [ ] Discuss pagination needs
- [ ] Discuss caching preferences

---

## 🎯 Conclusion

**Implementation Verdict**: ✅ **FULLY FEASIBLE**

**Why it's feasible:**
1. ✅ Database already stores historical data organized by scrape runs
2. ✅ `ScrapeRun.run_at` timestamp already exists
3. ✅ Relationships between tables support date-based queries
4. ✅ No architectural changes required
5. ✅ Can be implemented in 2-3 weeks with standard SQLAlchemy queries

**Recommended Approach:**
1. Start with Phase 1-3 (repository, models, service)
2. Add endpoints in Phase 4
3. Comprehensive testing in Phase 5
4. Collect feedback from frontend
5. Add Phase 6 enhancements as needed

**Next Step**: Meet with frontend team to confirm:
- Exact endpoint paths
- Response schema format
- Pagination requirements
- Go/no-go to begin implementation

---

**Created**: November 3, 2024
**Status**: Ready for Implementation
**Estimated Effort**: 2-3 weeks
**Team**: Backend (main), Frontend (integration)
