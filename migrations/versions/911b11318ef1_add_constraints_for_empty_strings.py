"""add constraints for empty strings

Revision ID: 911b11318ef1
Revises: 27b56cc8451c
Create Date: 2025-09-19 20:25:48.290940

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '911b11318ef1'
down_revision = '27b56cc8451c'
branch_labels = None
depends_on = None

# migrations generated manually! Alembic did not detect these changes.

def upgrade():
    # User table constraints
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_check_constraint(batch_op.f('user_email_non_empty_check'), "trim(email) != ''")
        batch_op.create_check_constraint(batch_op.f('user_email_normalized_non_empty_check'), "trim(email_normalized) != ''")
        batch_op.create_check_constraint(batch_op.f('user_password_hash_non_empty_check'), "trim(password_hash) != ''")

    # Category table constraint
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.create_check_constraint(batch_op.f('category_name_non_empty_check'), "trim(name) != ''")

    # Subcategory table constraint
    with op.batch_alter_table('subcategory', schema=None) as batch_op:
        batch_op.create_check_constraint(batch_op.f('subcategory_name_non_empty_check'), "trim(name) != ''")

    # Product table constraint
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.create_check_constraint(batch_op.f('product_name_non_empty_check'), "trim(name) != ''")


def downgrade():
    # Product table constraint
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('product_name_non_empty_check'), type_='check')

    # Subcategory table constraint
    with op.batch_alter_table('subcategory', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('subcategory_name_non_empty_check'), type_='check')

    # Category table constraint
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('category_name_non_empty_check'), type_='check')

    # User table constraints
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('user_password_hash_non_empty_check'), type_='check')
        batch_op.drop_constraint(batch_op.f('user_email_normalized_non_empty_check'), type_='check')
        batch_op.drop_constraint(batch_op.f('user_email_non_empty_check'), type_='check')
