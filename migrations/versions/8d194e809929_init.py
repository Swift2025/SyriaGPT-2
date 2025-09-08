"""Initial migration

Revision ID: 8d194e809929
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8d194e809929'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=False),
        sa.Column('two_factor_secret', sa.String(length=255), nullable=True),
        sa.Column('two_factor_backup_codes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('oauth_provider', sa.String(length=50), nullable=True),
        sa.Column('oauth_provider_id', sa.String(length=255), nullable=True),
        sa.Column('oauth_access_token', sa.Text(), nullable=True),
        sa.Column('oauth_refresh_token', sa.Text(), nullable=True),
        sa.Column('oauth_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('language_preference', sa.String(length=10), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(length=45), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notification_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_user_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('idx_user_oauth', 'users', ['oauth_provider', 'oauth_provider_id'], unique=False)
    op.create_index('idx_user_username_active', 'users', ['username', 'is_active'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('refresh_token', sa.String(length=255), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('security_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('refresh_token'),
        sa.UniqueConstraint('session_token')
    )
    op.create_index('idx_session_expires', 'user_sessions', ['expires_at'], unique=False)
    op.create_index('idx_session_last_activity', 'user_sessions', ['last_activity_at'], unique=False)
    op.create_index('idx_session_token_active', 'user_sessions', ['session_token', 'is_active'], unique=False)
    op.create_index('idx_session_user_active', 'user_sessions', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_user_sessions_refresh_token'), 'user_sessions', ['refresh_token'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=False)

    # Create chats table
    op.create_table('chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', 'DELETED', name='chatstatus'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_model', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('temperature', sa.String(length=10), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_created_at', 'chats', ['created_at'], unique=False)
    op.create_index('idx_chat_last_message', 'chats', ['last_message_at'], unique=False)
    op.create_index('idx_chat_user_status', 'chats', ['user_id', 'status'], unique=False)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', name='messagerole'), nullable=False),
        sa.Column('message_type', sa.Enum('TEXT', 'IMAGE', 'FILE', 'AUDIO', 'VIDEO', name='messagetype'), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('ai_model_used', sa.String(length=100), nullable=True),
        sa.Column('ai_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('original_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_message_chat_created', 'chat_messages', ['chat_id', 'created_at'], unique=False)
    op.create_index('idx_message_role', 'chat_messages', ['role'], unique=False)
    op.create_index('idx_message_type', 'chat_messages', ['message_type'], unique=False)

    # Create chat_feedback table
    op.create_table('chat_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.Enum('POSITIVE', 'NEGATIVE', 'NEUTRAL', name='feedbacktype'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_feedback_chat', 'chat_feedback', ['chat_id'], unique=False)
    op.create_index('idx_feedback_message', 'chat_feedback', ['message_id'], unique=False)
    op.create_index('idx_feedback_type', 'chat_feedback', ['feedback_type'], unique=False)
    op.create_index('idx_feedback_user', 'chat_feedback', ['user_id'], unique=False)

    # Create chat_settings table
    op.create_table('chat_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('default_ai_model', sa.String(length=100), nullable=False),
        sa.Column('default_language', sa.String(length=10), nullable=False),
        sa.Column('default_max_tokens', sa.Integer(), nullable=False),
        sa.Column('default_temperature', sa.String(length=10), nullable=False),
        sa.Column('auto_save_chats', sa.Boolean(), nullable=False),
        sa.Column('auto_delete_old_chats', sa.Boolean(), nullable=False),
        sa.Column('chat_retention_days', sa.Integer(), nullable=False),
        sa.Column('notify_on_new_message', sa.Boolean(), nullable=False),
        sa.Column('notify_on_chat_archived', sa.Boolean(), nullable=False),
        sa.Column('share_usage_data', sa.Boolean(), nullable=False),
        sa.Column('allow_ai_learning', sa.Boolean(), nullable=False),
        sa.Column('advanced_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_chat_settings_user', 'chat_settings', ['user_id'], unique=False)

    # Create qa_pairs table
    op.create_table('qa_pairs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('question_ar', sa.Text(), nullable=True),
        sa.Column('answer_ar', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('quality_rating', sa.Integer(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_title', sa.String(length=200), nullable=True),
        sa.Column('source_author', sa.String(length=200), nullable=True),
        sa.Column('embedding_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('processing_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False),
        sa.Column('dislike_count', sa.Integer(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.String(length=1), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_category', 'qa_pairs', ['category'], unique=False)
    op.create_index('idx_qa_confidence', 'qa_pairs', ['confidence_score'], unique=False)
    op.create_index('idx_qa_featured', 'qa_pairs', ['is_featured'], unique=False)
    op.create_index('idx_qa_last_used', 'qa_pairs', ['last_used_at'], unique=False)
    op.create_index('idx_qa_priority', 'qa_pairs', ['priority'], unique=False)
    op.create_index('idx_qa_public', 'qa_pairs', ['is_public'], unique=False)
    op.create_index('idx_qa_subcategory', 'qa_pairs', ['subcategory'], unique=False)
    op.create_index('idx_qa_verified', 'qa_pairs', ['verified'], unique=False)
    op.create_index('idx_qa_view_count', 'qa_pairs', ['view_count'], unique=False)
    op.create_index(op.f('ix_qa_pairs_category'), 'qa_pairs', ['category'], unique=False)
    op.create_index(op.f('ix_qa_pairs_subcategory'), 'qa_pairs', ['subcategory'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_qa_pairs_subcategory'), table_name='qa_pairs')
    op.drop_index(op.f('ix_qa_pairs_category'), table_name='qa_pairs')
    op.drop_index('idx_qa_view_count', table_name='qa_pairs')
    op.drop_index('idx_qa_verified', table_name='qa_pairs')
    op.drop_index('idx_qa_subcategory', table_name='qa_pairs')
    op.drop_index('idx_qa_public', table_name='qa_pairs')
    op.drop_index('idx_qa_priority', table_name='qa_pairs')
    op.drop_index('idx_qa_last_used', table_name='qa_pairs')
    op.drop_index('idx_qa_featured', table_name='qa_pairs')
    op.drop_index('idx_qa_confidence', table_name='qa_pairs')
    op.drop_index('idx_qa_category', table_name='qa_pairs')
    op.drop_table('qa_pairs')
    
    op.drop_index('idx_chat_settings_user', table_name='chat_settings')
    op.drop_table('chat_settings')
    
    op.drop_index('idx_feedback_user', table_name='chat_feedback')
    op.drop_index('idx_feedback_type', table_name='chat_feedback')
    op.drop_index('idx_feedback_message', table_name='chat_feedback')
    op.drop_index('idx_feedback_chat', table_name='chat_feedback')
    op.drop_table('chat_feedback')
    
    op.drop_index('idx_message_type', table_name='chat_messages')
    op.drop_index('idx_message_role', table_name='chat_messages')
    op.drop_index('idx_message_chat_created', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index('idx_chat_user_status', table_name='chats')
    op.drop_index('idx_chat_last_message', table_name='chats')
    op.drop_index('idx_chat_created_at', table_name='chats')
    op.drop_table('chats')
    
    op.drop_index(op.f('ix_user_sessions_session_token'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_refresh_token'), table_name='user_sessions')
    op.drop_index('idx_session_user_active', table_name='user_sessions')
    op.drop_index('idx_session_token_active', table_name='user_sessions')
    op.drop_index('idx_session_last_activity', table_name='user_sessions')
    op.drop_index('idx_session_expires', table_name='user_sessions')
    op.drop_table('user_sessions')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index('idx_user_username_active', table_name='users')
    op.drop_index('idx_user_oauth', table_name='users')
    op.drop_index('idx_user_email_active', table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS feedbacktype')
    op.execute('DROP TYPE IF EXISTS messagetype')
    op.execute('DROP TYPE IF EXISTS messagerole')
    op.execute('DROP TYPE IF EXISTS chatstatus')
