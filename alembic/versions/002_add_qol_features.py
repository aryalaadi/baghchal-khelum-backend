"""Add QoL features: user stats, game logs, and friends

Revision ID: 002
Revises: 001
Create Date: 2026-01-26 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add stats columns to users table
    op.add_column('users', sa.Column('games_played', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('games_won', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('games_lost', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('games_drawn', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('goats_captured_total', sa.Integer(), server_default='0', nullable=False))
    
    # Create friends association table
    op.create_table(
        'friends',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'friend_id')
    )
    
    # Create game_logs table
    op.create_table(
        'game_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.String(), nullable=False),
        sa.Column('tiger_player_id', sa.Integer(), nullable=False),
        sa.Column('goat_player_id', sa.Integer(), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('result', sa.String(), nullable=False),
        sa.Column('goats_captured', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_moves', sa.Integer(), server_default='0', nullable=False),
        sa.Column('game_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('tiger_elo_before', sa.Float(), nullable=False),
        sa.Column('tiger_elo_after', sa.Float(), nullable=False),
        sa.Column('goat_elo_before', sa.Float(), nullable=False),
        sa.Column('goat_elo_after', sa.Float(), nullable=False),
        sa.Column('moves_history', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tiger_player_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['goat_player_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_logs_id'), 'game_logs', ['id'], unique=False)
    op.create_index(op.f('ix_game_logs_match_id'), 'game_logs', ['match_id'], unique=False)
    
    # Create friend_challenges table
    op.create_table(
        'friend_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenger_id', sa.Integer(), nullable=False),
        sa.Column('challenged_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'DECLINED', 'EXPIRED', name='challengestatus'), nullable=True),
        sa.Column('match_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['challenger_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['challenged_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_friend_challenges_id'), 'friend_challenges', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_friend_challenges_id'), table_name='friend_challenges')
    op.drop_table('friend_challenges')
    op.drop_index(op.f('ix_game_logs_match_id'), table_name='game_logs')
    op.drop_index(op.f('ix_game_logs_id'), table_name='game_logs')
    op.drop_table('game_logs')
    op.drop_table('friends')
    
    # Remove columns from users table
    op.drop_column('users', 'goats_captured_total')
    op.drop_column('users', 'games_drawn')
    op.drop_column('users', 'games_lost')
    op.drop_column('users', 'games_won')
    op.drop_column('users', 'games_played')
    
    # Drop enum type
    sa.Enum(name='challengestatus').drop(op.get_bind(), checkfirst=True)
