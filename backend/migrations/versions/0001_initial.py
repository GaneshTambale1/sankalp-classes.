"""Initial versioned schema, based on SQLAlchemy models.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
from app.extensions import db
revision='0001_initial'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    db.metadata.create_all(bind=op.get_bind(),checkfirst=True)

def downgrade():
    db.metadata.drop_all(bind=op.get_bind(),checkfirst=True)
