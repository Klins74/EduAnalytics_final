"""Add schedule, events and classrooms tables

Revision ID: 89c4b8a7d12f
Revises: 75285fe7e166
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89c4b8a7d12f'
down_revision: Union[str, Sequence[str], None] = '75285fe7e166'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (idempotent where possible)."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- Classrooms table ---
    if not insp.has_table('classrooms'):
        op.create_table(
            'classrooms',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('building', sa.String(length=100), nullable=True),
            sa.Column('floor', sa.Integer(), nullable=True),
            sa.Column('capacity', sa.Integer(), nullable=True),
            sa.Column('equipment', sa.Text(), nullable=True),
            sa.Column('is_available', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_classrooms_id'), 'classrooms', ['id'], unique=False)
        op.create_index(op.f('ix_classrooms_name'), 'classrooms', ['name'], unique=True)
    else:
        # Ensure unique index on name exists
        idx_names = {ix['name'] for ix in insp.get_indexes('classrooms')}
        if 'ix_classrooms_name' not in idx_names:
            op.create_index(op.f('ix_classrooms_name'), 'classrooms', ['name'], unique=True)

    # --- Schedules table ---
    # Надёжное создание ENUM lessontype (идемпотентно, вне транзакции)
    import psycopg2
    import os
    db_url = os.getenv("DATABASE_URL") or "postgresql://edua:secret@db:5432/eduanalytics"
    try:
        with psycopg2.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_type WHERE typname = 'lessontype'")
                if cur.fetchone() is None:
                    cur.execute("CREATE TYPE lessontype AS ENUM ('lecture', 'seminar', 'laboratory', 'practical', 'exam', 'consultation', 'other')")
    except Exception as e:
        print(f"[Alembic ENUM] {e}")
    if not insp.has_table('schedules'):
        op.create_table(
            'schedules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('schedule_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=False),
            sa.Column('location', sa.String(length=200), nullable=True),
            sa.Column('instructor_id', sa.Integer(), nullable=False),
            sa.Column('lesson_type', sa.Enum('lecture', 'seminar', 'laboratory', 'practical', 'exam', 'consultation', 'other', name='lessontype'), nullable=False, server_default='lecture'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_cancelled', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('classroom_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id']),
            sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
            sa.ForeignKeyConstraint(['instructor_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)
        op.create_index(op.f('ix_schedules_course_id'), 'schedules', ['course_id'], unique=False)
        op.create_index(op.f('ix_schedules_schedule_date'), 'schedules', ['schedule_date'], unique=False)
        # Drop server defaults to mimic model behavior
        with op.batch_alter_table('schedules') as batch_op:
            batch_op.alter_column('lesson_type', server_default=None)
            batch_op.alter_column('is_cancelled', server_default=None)
    else:
        # Table exists; ensure new columns/indexes/constraints are present
        cols = {c['name'] for c in insp.get_columns('schedules')}
        idx_names = {ix['name'] for ix in insp.get_indexes('schedules')}
        fks = insp.get_foreign_keys('schedules')
        fk_cols = {tuple(fk.get('constrained_columns', [])) for fk in fks}

        # Add missing columns using batch mode for SQLite compatibility
        with op.batch_alter_table('schedules') as batch_op:
            if 'lesson_type' not in cols:
                batch_op.add_column(sa.Column('lesson_type', sa.Enum('lecture', 'seminar', 'laboratory', 'practical', 'exam', 'consultation', 'other', name='lessontype'), nullable=False, server_default='lecture'))
                batch_op.alter_column('lesson_type', server_default=None)
            if 'description' not in cols:
                batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
            if 'notes' not in cols:
                batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
            if 'is_cancelled' not in cols:
                batch_op.add_column(sa.Column('is_cancelled', sa.Integer(), nullable=False, server_default=sa.text('0')))
                batch_op.alter_column('is_cancelled', server_default=None)
            if 'classroom_id' not in cols:
                batch_op.add_column(sa.Column('classroom_id', sa.Integer(), nullable=True))
                # Add FK if not exists
                if ('classroom_id',) not in fk_cols:
                    try:
                        batch_op.create_foreign_key('fk_schedules_classroom_id_classrooms', 'classrooms', ['classroom_id'], ['id'])
                    except Exception:
                        pass
        # Ensure indexes
        if 'ix_schedules_course_id' not in idx_names:
            op.create_index(op.f('ix_schedules_course_id'), 'schedules', ['course_id'], unique=False)
        if 'ix_schedules_schedule_date' not in idx_names:
            op.create_index(op.f('ix_schedules_schedule_date'), 'schedules', ['schedule_date'], unique=False)

    # --- Events table ---
    if not insp.has_table('events'):
        op.create_table(
            'events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('event_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=False),
            sa.Column('location', sa.String(length=200), nullable=True),
            sa.Column('organizer_id', sa.Integer(), nullable=False),
            sa.Column('is_public', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['organizer_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
        op.create_index(op.f('ix_events_event_date'), 'events', ['event_date'], unique=False)
        with op.batch_alter_table('events') as batch_op:
            batch_op.alter_column('is_public', server_default=None)
    else:
        idx_names = {ix['name'] for ix in insp.get_indexes('events')}
        if 'ix_events_event_date' not in idx_names:
            op.create_index(op.f('ix_events_event_date'), 'events', ['event_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop events table if exists
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table('events'):
        try:
            op.drop_index(op.f('ix_events_event_date'), table_name='events')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_events_id'), table_name='events')
        except Exception:
            pass
        op.drop_table('events')

    # Drop schedules table if exists
    if insp.has_table('schedules'):
        try:
            op.drop_index(op.f('ix_schedules_schedule_date'), table_name='schedules')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_schedules_course_id'), table_name='schedules')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_schedules_id'), table_name='schedules')
        except Exception:
            pass
        op.drop_table('schedules')

    # Drop classrooms table if exists
    if insp.has_table('classrooms'):
        try:
            op.drop_index(op.f('ix_classrooms_name'), table_name='classrooms')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_classrooms_id'), table_name='classrooms')
        except Exception:
            pass
        op.drop_table('classrooms')