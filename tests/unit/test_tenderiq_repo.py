
from app.db.database import SessionLocal, get_db_session
from app.modules.tenderiq.db.schema import Tender
from app.modules.tenderiq.db.tenderiq_repository import TenderIQRepository

db = SessionLocal()

test = db.query(Tender).all()
print(test)

exit()
repo = TenderIQRepository(db)
scrape_runs = repo.get_scrape_runs_by_date_range(days=None)
print(scrape_runs)

