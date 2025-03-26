"""add_employee_and_supervisor_numbers

Revision ID: cdc692568ccc
Revises: 
Create Date: 2025-03-23

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = 'cdc692568ccc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Para SQLite, usamos batch_alter_table en lugar de op.add_column directamente
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('employee_number', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('supervisor_number', sa.String(), nullable=True))
    
    # Si hay alguna operación con constraints, también usar batch_alter_table
    # Por ejemplo, si necesitas agregar la restricción única al role_name:
    # with op.batch_alter_table('role', schema=None) as batch_op:
    #     batch_op.create_unique_constraint(None, ['role_name'])


def downgrade() -> None:
    # Para SQLite, usamos batch_alter_table en lugar de op.drop_column directamente
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('supervisor_number')
        batch_op.drop_column('employee_number')
    
    # Si se agregaron constraints, aquí también usamos batch_alter_table para eliminarlos
    # with op.batch_alter_table('role', schema=None) as batch_op:
    #     batch_op.drop_constraint(None, type_='unique')