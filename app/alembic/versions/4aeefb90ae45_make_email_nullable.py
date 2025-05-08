"""make_email_nullable

Revision ID: 4aeefb90ae45
Revises: [previous_revision_id]  # Check your migrations folder for the actual ID
Create Date: 2025-05-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '4aeefb90ae45'
down_revision = None  # Replace with the actual previous revision ID if any
branch_labels = None
depends_on = None


def upgrade():
    """Make email field nullable in user table."""
    # SQLite doesn't support ALTER COLUMN directly with NOT NULL changes,
    # so we need to use batch operations
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('email',
                            existing_type=sa.VARCHAR(255),
                            nullable=True)


def downgrade():
    """Make email field not nullable again in user table."""
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('email',
                            existing_type=sa.VARCHAR(255),
                            nullable=False)