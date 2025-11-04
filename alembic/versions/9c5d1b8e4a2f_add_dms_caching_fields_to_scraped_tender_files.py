"""Add DMS caching fields to scraped_tender_files

This migration supports the new hybrid file storage strategy:
- Files are NOT downloaded during scraping (saving 12 hours and storage)
- file_url stores the original internet location
- dms_path stores the reference in DMS
- DMS module handles remote vs local file logic transparently

Adds:
- dms_path: Reference path in DMS where file can be cached
- is_cached: Boolean flag if file is downloaded locally
- cache_status: Current state (pending, cached, failed)
- cache_error: Error message if caching failed

Revision ID: 9c5d1b8e4a2f
Revises: 8a4f7c9b2d1e
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c5d1b8e4a2f'
down_revision = '8a4f7c9b2d1e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add new columns for DMS caching strategy
    op.add_column('scraped_tender_files', sa.Column('dms_path', sa.String(), nullable=True))
    op.add_column('scraped_tender_files', sa.Column('is_cached', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('scraped_tender_files', sa.Column('cache_status', sa.String(), nullable=True, server_default='pending'))
    op.add_column('scraped_tender_files', sa.Column('cache_error', sa.Text(), nullable=True))

    # Step 2: Create indexes for efficient querying
    op.create_index(
        'idx_file_cache_status',
        'scraped_tender_files',
        ['cache_status'],
        unique=False
    )
    op.create_index(
        'idx_file_dms_path',
        'scraped_tender_files',
        ['dms_path'],
        unique=False
    )

    # Step 3: Populate dms_path with default values based on tender and filename
    # This generates paths like: /dms/tenders/YYYY/MM/DD/tender_id/files/filename
    op.execute("""
        UPDATE scraped_tender_files
        SET dms_path = '/dms/tenders/' ||
                       TO_CHAR(sr.tender_release_date, 'YYYY/MM/DD') || '/' ||
                       st.id::text || '/files/' ||
                       file_name
        FROM scraped_tender_queries stq
        JOIN scraped_tenders st ON st.query_id = stq.id
        JOIN scrape_runs sr ON sr.id = stq.scrape_run_id
        WHERE scraped_tender_files.tender_id = st.id
        AND dms_path IS NULL
    """)

    # Step 4: Make columns NOT NULL after populating
    op.alter_column('scraped_tender_files', 'dms_path',
                    existing_type=sa.String(),
                    nullable=False)
    op.alter_column('scraped_tender_files', 'is_cached',
                    existing_type=sa.Boolean(),
                    nullable=False)
    op.alter_column('scraped_tender_files', 'cache_status',
                    existing_type=sa.String(),
                    nullable=False)

    # Step 5: Make file_url NOT NULL (it should have been already, but ensure it)
    op.alter_column('scraped_tender_files', 'file_url',
                    existing_type=sa.String(),
                    nullable=False)
    op.alter_column('scraped_tender_files', 'file_name',
                    existing_type=sa.String(),
                    nullable=False)


def downgrade() -> None:
    # Reverse the changes
    op.drop_index('idx_file_dms_path', table_name='scraped_tender_files')
    op.drop_index('idx_file_cache_status', table_name='scraped_tender_files')
    op.drop_column('scraped_tender_files', 'cache_error')
    op.drop_column('scraped_tender_files', 'cache_status')
    op.drop_column('scraped_tender_files', 'is_cached')
    op.drop_column('scraped_tender_files', 'dms_path')
