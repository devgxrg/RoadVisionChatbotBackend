from typing import Optional
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from app.modules.scraper.db.schema import ScrapedTender
from app.modules.tenderiq.models.pydantic_models import DailyTendersResponse

def get_latest_daily_tenders(db: Session) -> Optional[DailyTendersResponse]:
    """Fetches the latest scrape run and formats it for the API response."""
    from app.modules.scraper.db.repository import ScraperRepository
    scraper_repo = ScraperRepository(db)
    latest_run = scraper_repo.get_latest_scrape_run()
    if not latest_run:
        return None
    return DailyTendersResponse.model_validate(latest_run)


def get_full_tender_details(db: Session, tender_id: UUID):
    """
    Fetch full tender details with all related files eagerly loaded.
    """
    scraped_tender = db.query(ScrapedTender).options(
        joinedload(ScrapedTender.files)  # Eagerly load files
    ).filter(
        ScrapedTender.id == tender_id
    ).first()
    
    return scraped_tender
