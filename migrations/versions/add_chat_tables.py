"""Add chat tables

Revision ID: add_chat_tables
Revises: add_oauth_token_fields
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_chat_tables'
down_revision = 'add_oauth_token_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create chats table
    op.create_table('chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('model_preference', sa.String(length=50), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False),
        sa.Column('attachments', postgresql.JSON(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('is_ai_response', sa.Boolean(), nullable=False),
        sa.Column('ai_model_used', sa.String(length=50), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('feedback_rating', sa.Integer(), nullable=True),
        sa.Column('feedback_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chat_feedbacks table
    op.create_table('chat_feedbacks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chat_settings table
    op.create_table('chat_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('default_language', sa.String(length=10), nullable=False),
        sa.Column('default_model', sa.String(length=50), nullable=False),
        sa.Column('default_max_tokens', sa.Integer(), nullable=False),
        sa.Column('default_temperature', sa.Float(), nullable=False),
        sa.Column('auto_archive_after_days', sa.Integer(), nullable=False),
        sa.Column('max_chats_per_user', sa.Integer(), nullable=False),
        sa.Column('max_messages_per_chat', sa.Integer(), nullable=False),
        sa.Column('enable_voice_input', sa.Boolean(), nullable=False),
        sa.Column('enable_file_upload', sa.Boolean(), nullable=False),
        sa.Column('enable_image_analysis', sa.Boolean(), nullable=False),
        sa.Column('enable_context_memory', sa.Boolean(), nullable=False),
        sa.Column('enable_chat_history', sa.Boolean(), nullable=False),
        sa.Column('enable_analytics', sa.Boolean(), nullable=False),
        sa.Column('enable_feedback', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_chats_user_id'), 'chats', ['user_id'], unique=False)
    op.create_index(op.f('ix_chats_created_at'), 'chats', ['created_at'], unique=False)
    op.create_index(op.f('ix_chats_updated_at'), 'chats', ['updated_at'], unique=False)
    op.create_index(op.f('ix_chats_is_archived'), 'chats', ['is_archived'], unique=False)
    op.create_index(op.f('ix_chats_is_pinned'), 'chats', ['is_pinned'], unique=False)
    
    op.create_index(op.f('ix_chat_messages_chat_id'), 'chat_messages', ['chat_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_user_id'), 'chat_messages', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_is_ai_response'), 'chat_messages', ['is_ai_response'], unique=False)
    
    op.create_index(op.f('ix_chat_feedbacks_message_id'), 'chat_feedbacks', ['message_id'], unique=False)
    op.create_index(op.f('ix_chat_feedbacks_user_id'), 'chat_feedbacks', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_feedbacks_created_at'), 'chat_feedbacks', ['created_at'], unique=False)
    
    op.create_index(op.f('ix_chat_settings_user_id'), 'chat_settings', ['user_id'], unique=True)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_chat_settings_user_id'), table_name='chat_settings')
    op.drop_index(op.f('ix_chat_feedbacks_created_at'), table_name='chat_feedbacks')
    op.drop_index(op.f('ix_chat_feedbacks_user_id'), table_name='chat_feedbacks')
    op.drop_index(op.f('ix_chat_feedbacks_message_id'), table_name='chat_feedbacks')
    op.drop_index(op.f('ix_chat_messages_is_ai_response'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_created_at'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_user_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_chat_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chats_is_pinned'), table_name='chats')
    op.drop_index(op.f('ix_chats_is_archived'), table_name='chats')
    op.drop_index(op.f('ix_chats_updated_at'), table_name='chats')
    op.drop_index(op.f('ix_chats_created_at'), table_name='chats')
    op.drop_index(op.f('ix_chats_user_id'), table_name='chats')
    
    # Drop tables
    op.drop_table('chat_settings')
    op.drop_table('chat_feedbacks')
    op.drop_table('chat_messages')
    op.drop_table('chats')

