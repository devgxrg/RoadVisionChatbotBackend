
from app.modules.scraper.data_models import TenderDetailPage
from app.core.services import vector_store, pdf_processor


def start_tender_processing(tender: TenderDetailPage):
    """
    1. This function will download every file in the tender detail page, process them and save them in the
    vector database
    2. It will then perform some additional LLM magic on them and add them to the tender_analysis table
    """

    # 1. Download files to temporary storage
    # 2. Text extraction
    # 3. Chunking
    # 4. Vectorization
    # 5. LLM magic

    pass
