"""empty message

Revision ID: 3e19c8d3e621
Revises: 
Create Date: 2019-12-09 14:01:59.444396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e19c8d3e621'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('user_image_url', sa.String(length=120), nullable=True),
    sa.Column('twitter_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('twitter_id')
    )
    op.create_index(op.f('ix_user_user_image_url'), 'user', ['user_image_url'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.drop_table('ID')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ID',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"ID_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('max_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('MAX_ID', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('NEXT_MAX_ID', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='ID_pkey')
    )
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_user_image_url'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###