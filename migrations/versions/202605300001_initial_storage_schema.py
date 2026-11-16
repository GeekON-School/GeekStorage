"""initial storage schema

Revision ID: 202605300001
Revises:
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '202605300001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'file_blobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('storage_backend', sa.String(length=20), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('storage_name', sa.String(length=255), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('checksum_sha256'),
        sa.UniqueConstraint('storage_name'),
    )
    op.create_index(op.f('ix_file_blobs_checksum_sha256'), 'file_blobs', ['checksum_sha256'], unique=False)
    op.create_index(op.f('ix_file_blobs_storage_name'), 'file_blobs', ['storage_name'], unique=False)
    op.create_table(
        'user_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_id', sa.String(length=32), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('blob_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=512), nullable=False),
        sa.Column('safe_filename', sa.String(length=512), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['blob_id'], ['file_blobs.id']),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_user_id', 'original_filename', name='uq_user_files_owner_filename'),
        sa.UniqueConstraint('public_id'),
    )
    op.create_index(op.f('ix_user_files_blob_id'), 'user_files', ['blob_id'], unique=False)
    op.create_index(op.f('ix_user_files_checksum_sha256'), 'user_files', ['checksum_sha256'], unique=False)
    op.create_index(op.f('ix_user_files_owner_user_id'), 'user_files', ['owner_user_id'], unique=False)
    op.create_index(op.f('ix_user_files_public_id'), 'user_files', ['public_id'], unique=False)
    op.create_table(
        'file_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('public_path', sa.String(length=512), nullable=False),
        sa.Column('blob_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=512), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['blob_id'], ['file_blobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_path'),
    )
    op.create_index(op.f('ix_file_aliases_blob_id'), 'file_aliases', ['blob_id'], unique=False)
    op.create_index(op.f('ix_file_aliases_checksum_sha256'), 'file_aliases', ['checksum_sha256'], unique=False)
    op.create_index(op.f('ix_file_aliases_public_path'), 'file_aliases', ['public_path'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_file_aliases_public_path'), table_name='file_aliases')
    op.drop_index(op.f('ix_file_aliases_checksum_sha256'), table_name='file_aliases')
    op.drop_index(op.f('ix_file_aliases_blob_id'), table_name='file_aliases')
    op.drop_table('file_aliases')
    op.drop_index(op.f('ix_user_files_public_id'), table_name='user_files')
    op.drop_index(op.f('ix_user_files_owner_user_id'), table_name='user_files')
    op.drop_index(op.f('ix_user_files_checksum_sha256'), table_name='user_files')
    op.drop_index(op.f('ix_user_files_blob_id'), table_name='user_files')
    op.drop_table('user_files')
    op.drop_index(op.f('ix_file_blobs_storage_name'), table_name='file_blobs')
    op.drop_index(op.f('ix_file_blobs_checksum_sha256'), table_name='file_blobs')
    op.drop_table('file_blobs')
    op.drop_table('users')
