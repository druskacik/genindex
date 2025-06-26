"""init

Revision ID: c632902fb8e5
Revises: 
Create Date: 2025-06-26 17:20:32.680121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c632902fb8e5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'post',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('url', sa.String, nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('content', sa.String, nullable=False),
        sa.Column('text', sa.String, nullable=True),
        sa.Column('response', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_table(
        'post_url',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('post_id', sa.String, sa.ForeignKey('post.id'), nullable=False),
        sa.Column('domain', sa.String, nullable=False),
        sa.Column('url', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    op.create_table(
        'post_query',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('post_id', sa.String, sa.ForeignKey('post.id'), nullable=False),
        sa.Column('query', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('post_query')
    op.drop_table('post_url')
    op.drop_table('post')
