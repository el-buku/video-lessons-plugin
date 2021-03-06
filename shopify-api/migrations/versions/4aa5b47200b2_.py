"""empty message

Revision ID: 4aa5b47200b2
Revises: 
Create Date: 2020-07-08 17:18:15.945985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4aa5b47200b2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('shop',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_name', sa.String(), nullable=False),
    sa.Column('shop_token', sa.String(), nullable=False),
    sa.Column('webhook_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('room',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('room_id', sa.Integer(), nullable=False),
    sa.Column('room_name', sa.String(), nullable=True),
    sa.Column('instructor_id', sa.Integer(), nullable=False),
    sa.Column('sku', sa.String(), nullable=False),
    sa.Column('variant_title', sa.String(), nullable=False),
    sa.Column('user_pass_list', sa.String(), nullable=True),
    sa.Column('admin_pass', sa.String(), nullable=True),
    sa.Column('sent_pass_list', sa.String(), nullable=True),
    sa.Column('started', sa.Boolean(), nullable=False),
    sa.Column('link', sa.String(), nullable=True),
    sa.Column('count', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shop.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('room')
    op.drop_table('shop')
    # ### end Alembic commands ###
