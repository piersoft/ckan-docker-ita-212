"""Remove indexes in vocab

Revision ID: d54a365195ea
Revises: cfd1d82a53fe
Create Date: 2022-03-17 12:06:10.611576

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd54a365195ea'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Using op.execute in order not to raise error in case the index/constraint is not there

    # op.drop_index('ix_dcatapit_vocabulary_text', 'dcatapit_vocabulary')
    op.execute('DROP INDEX IF EXISTS ix_dcatapit_vocabulary_text')

    # op.drop_constraint('dcatapit_subtheme_path_key', 'dcatapit_subtheme')
    # CKAN >= 2.11 esegue le migrazioni dei plugin durante `ckan db upgrade`,
    # cioe' PRIMA di `ckan dcatapit initdb`: la tabella puo' non esistere ancora.
    op.execute("""
        DO $$ BEGIN
            IF to_regclass('dcatapit_subtheme') IS NOT NULL THEN
                ALTER TABLE dcatapit_subtheme DROP CONSTRAINT IF EXISTS dcatapit_subtheme_path_key;
            END IF;
        END $$;
    """)


def downgrade():
    op.create_index('ix_dcatapit_vocabulary_text', 'dcatapit_vocabulary', ['text'])
    op.create_unique_constraint('dcatapit_subtheme_path_key', 'dcatapit_subtheme', ['path'])

