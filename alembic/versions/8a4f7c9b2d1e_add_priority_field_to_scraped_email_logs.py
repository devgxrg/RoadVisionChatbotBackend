"""Add priority field to scraped_email_logs for conflict resolution

This migration adds a priority field to support email priority handling
when the same tender is submitted through multiple sources (email and manual).

Enables unified deduplication across both email and manual link pasting modes,
with ability to prioritize specific emails or manual submissions.

Revision ID: 8a4f7c9b2d1e
Revises: 642bfe5074f2e
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a4f7c9b2d1e'
down_revision = '642bfe5074f2e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add priority column with default value "normal"
    op.add_column('scraped_email_logs', sa.Column('priority', sa.String(), nullable=False, server_default='normal'))

    # Step 2: Create index for priority-based conflict resolution
    op.create_index(
        'idx_tender_url_priority',
        'scraped_email_logs',
        ['tender_url', 'priority'],
        unique=False
    )

    # Step 3: Update processing_status enum to include "superseded" status
    # This is handled by the column already having String type (no enum restriction)
    # No SQL changes needed - "superseded" can be inserted without schema changes


def downgrade() -> None:
    # Reverse the changes
    op.drop_index('idx_tender_url_priority', table_name='scraped_email_logs')
    op.drop_column('scraped_email_logs', 'priority')
