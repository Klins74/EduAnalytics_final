"""Add notification logging and DLQ tables

Revision ID: notification_dlq_001
Revises: previous_revision
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'notification_dlq_001'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Create notification logging and DLQ tables."""
    
    # Notification log table
    op.create_table(
        'notification_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('idempotency_key', sa.String(64), nullable=False, index=True),
        sa.Column('recipient_id', sa.Integer, nullable=False, index=True),
        sa.Column('channel', sa.String(20), nullable=False, index=True),
        sa.Column('recipient_address', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('template_id', sa.String(50), nullable=True),
        sa.Column('template_data', sa.JSON, nullable=True),
        sa.Column('priority', sa.Integer, nullable=False, default=3),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, default=0),
        sa.Column('max_retries', sa.Integer, nullable=False, default=3),
        sa.Column('retry_strategy', sa.String(20), nullable=False, default='exponential_backoff'),
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
    )
    
    # Delivery attempts table
    op.create_table(
        'notification_delivery_attempts',
        sa.Column('attempt_id', sa.String(36), primary_key=True),
        sa.Column('message_id', sa.String(36), sa.ForeignKey('notification_log.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('attempt_number', sa.Integer, nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('response_code', sa.String(10), nullable=True),
        sa.Column('response_message', sa.Text, nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('error_details', sa.Text, nullable=True),
    )
    
    # Indexes for performance
    op.create_index('idx_notification_log_channel_status', 'notification_log', ['channel', 'status'])
    op.create_index('idx_notification_log_created_status', 'notification_log', ['created_at', 'status'])
    op.create_index('idx_notification_log_recipient_channel', 'notification_log', ['recipient_id', 'channel'])
    op.create_index('idx_notification_log_priority_created', 'notification_log', ['priority', 'created_at'])
    
    op.create_index('idx_delivery_attempts_message_attempt', 'notification_delivery_attempts', ['message_id', 'attempt_number'])
    op.create_index('idx_delivery_attempts_attempted_status', 'notification_delivery_attempts', ['attempted_at', 'status'])
    
    # Unique constraint for idempotency
    op.create_index('idx_notification_log_idempotency_unique', 'notification_log', ['idempotency_key'], unique=True)


def downgrade():
    """Drop notification logging and DLQ tables."""
    
    # Drop indexes first
    op.drop_index('idx_notification_log_idempotency_unique')
    op.drop_index('idx_delivery_attempts_attempted_status')
    op.drop_index('idx_delivery_attempts_message_attempt')
    op.drop_index('idx_notification_log_priority_created')
    op.drop_index('idx_notification_log_recipient_channel')
    op.drop_index('idx_notification_log_created_status')
    op.drop_index('idx_notification_log_channel_status')
    
    # Drop tables
    op.drop_table('notification_delivery_attempts')
    op.drop_table('notification_log')
