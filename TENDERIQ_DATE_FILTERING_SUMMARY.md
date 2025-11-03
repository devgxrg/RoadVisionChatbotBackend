# TenderIQ Date Filtering - Quick Summary

## ✅ Feasibility: FULLY POSSIBLE

All the data you need is **already in the database**. No major architectural changes needed.

---

## 📊 What Frontend Wants

```
User Actions:
├─ Select "Last 5 Days" → Shows tenders from past 5 days
├─ Select specific date from dropdown → Shows tenders from that date
├─ Select "All Dates" → Shows entire historical database
└─ Additional filters: Category, Location, Value Range
```

---

## 🗄️ Why It's Feasible

### Current Database Structure
```
ScrapeRun (has timestamp: run_at)
    ├─ id (UUID)
    ├─ run_at (DateTime) ← THE KEY FIELD
    ├─ date_str (String) ← "November 3, 2024"
    └─ relationships to queries/tenders

ScrapedTenderQuery
    └─ tenders (can filter by scrape run date)
```

**Key Point**: Every tender is linked to a `ScrapeRun` which has a timestamp.
Querying by date is just: "Give me all tenders from scrape runs between date X and Y"

---

## 🔧 What Needs to Be Built

### 1. **Repository Layer** (2-3 days)
Add query methods to `ScraperRepository`:
```python
get_scrape_runs_by_date_range(days=5)  # Last 5 days
get_tenders_by_specific_date(date="2024-11-03")
get_available_scrape_runs()  # For dropdown
get_tenders_by_scrape_run(id, category=None, location=None)
```

### 2. **Pydantic Models** (1-2 days)
Create response schemas:
```python
TenderResponse
ScrapeDateInfo
AvailableDatesResponse
FilteredTendersResponse
```

### 3. **Service Layer** (2-3 days)
`TenderFilterService` with methods:
```python
get_available_dates()
get_tenders_by_date_range(date_range, filters)
get_tenders_by_specific_date(date, filters)
get_all_tenders(filters)
```

### 4. **API Endpoints** (1-2 days)
Two new endpoints:
```
GET /api/v1/tenderiq/dates
    → Returns: List of all available dates with tender counts

GET /api/v1/tenderiq/tenders
    Query params: date, date_range, include_all_dates, category, location, min_value, max_value
    → Returns: Filtered tenders + metadata
```

### 5. **Tests** (2-3 days)
Unit + integration tests covering:
- Date range filtering
- Specific date filtering
- Filter combinations
- Edge cases

---

## 📅 Timeline

| Phase | Duration | Work |
|-------|----------|------|
| Database & Models | 3-4 days | Repository + Pydantic models |
| Service & Endpoints | 2-3 days | Filter service + 2 new endpoints |
| Testing | 2-3 days | Unit + integration tests |
| **Total** | **2-3 weeks** | Ready to deploy |

---

## 🚫 Challenges (Minor)

### Challenge 1: Date String Storage
Currently `due_date`, `publish_date` are stored as **Strings**, not DateTime.
- ❌ Can't filter by "tenders due in next 7 days"
- ✅ CAN filter by "tenders scraped in last 5 days" ← What frontend wants

**Impact**: None - matches what frontend requested

### Challenge 2: Large Result Sets
If user selects "All Dates" and DB has 100k tenders:
- ⚠️ Could be slow without pagination
- ✅ Can add pagination in Phase 2

**Impact**: Minor - recommend pagination as Phase 6 enhancement

### Challenge 3: Response Format
Need to confirm format matches `TENDERIQ_API_SUGGESTIONS.json`
- ⚠️ Currently not specified in detail
- ✅ Roadmap assumes spec format is correct

**Impact**: None if spec is confirmed

---

## 💡 Quick Code Examples

### Repository Method Example
```python
def get_scrape_runs_by_date_range(self, days: Optional[int] = None):
    from datetime import datetime, timedelta

    query = self.db.query(ScrapeRun)

    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = query.filter(ScrapeRun.run_at >= cutoff_date)

    return query.order_by(ScrapeRun.run_at.desc()).all()
```

### Endpoint Example
```python
@router.get("/tenders")
def get_filtered_tenders(
    db: Session = Depends(get_db_session),
    date: Optional[str] = Query(None),
    date_range: Optional[str] = Query(None),
    include_all_dates: bool = Query(False),
):
    service = TenderFilterService()

    if include_all_dates:
        return service.get_all_tenders(db)
    elif date:
        return service.get_tenders_by_specific_date(db, date)
    elif date_range:
        days = {"last_1_day": 1, "last_5_days": 5}.get(date_range)
        return service.get_tenders_by_date_range(db, days)
```

---

## 🎯 Implementation Priority

### Must Have (Week 1-2)
- [x] Repository date range queries
- [x] Service layer
- [x] Both endpoints
- [x] Basic tests

### Nice to Have (Week 3+)
- [ ] Pagination
- [ ] Sorting
- [ ] Caching
- [ ] Advanced filters
- [ ] Performance optimization

---

## 📱 Frontend Integration

### Step 1: Get Available Dates
```javascript
const dates = await fetch('/api/v1/tenderiq/dates')
// Populates date selector dropdown
```

### Step 2: Fetch Based on Selection
```javascript
const tenders = await fetch(`/api/v1/tenderiq/tenders?date_range=last_5_days`)
// Shows filtered results
```

---

## 🔐 No Security Changes Needed
- Use existing auth (same as `/dailytenders`)
- No new permissions required
- No sensitive data exposed

---

## ✨ Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| Feasibility | ✅ Fully Possible | Data already exists |
| Complexity | 🟡 Medium | Standard SQLAlchemy queries |
| Duration | 2-3 weeks | With testing |
| Risk Level | 🟢 Low | No architectural changes |
| Breaking Changes | ✅ None | New endpoints only |
| Frontend Ready | ❓ TBD | Confirm format needed |

---

## 🚀 Next Steps

1. ✅ Review this roadmap
2. ❓ Confirm response format with frontend
3. ❓ Discuss optional features (pagination, caching)
4. ✅ Get go/no-go approval
5. 🔨 Begin implementation (Week 1: Database & Models)

---

**For Detailed Implementation**: See [TENDERIQ_DATE_FILTERING_ROADMAP.md](./TENDERIQ_DATE_FILTERING_ROADMAP.md)
