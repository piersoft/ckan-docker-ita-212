import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import and_

import ckan.plugins.toolkit as toolkit
from ckan.common import config
from ckan.lib.navl.dictization_functions import Invalid
from ckan.logic import ValidationError
from ckan.logic.validators import tag_name_validator
from ckan.model.meta import Session
from ckan.model import (
    Group,
    Package,
    repo,
)

from ckanext.dcatapit.schema import FIELD_THEMES_AGGREGATE
from ckanext.dcatapit import validators
import ckanext.dcatapit.interfaces as interfaces

REGION_TYPE = 'https://w3id.org/italia/onto/CLV/Region'
NAME_TYPE = 'https://w3id.org/italia/onto/l0/name'

DEFAULT_LANG = config.get('ckan.locale_default', 'en')
DATE_FORMAT = '%d-%m-%Y'

log = logging.getLogger(__name__)


def migrate(fix_old=False):
    # Data migrations from 1.1.0 to 2.0.0

    cnt_migrated = migrate_themes()
    cnt_obsolete_found, cnt_obsolete_migrated = check_obsolete_themes(fix_old)

    log.info(f'========== Migration summary ==========')
    log.info(f'Migrated theme extra keys: {cnt_migrated}')
    log.info(f'Obsolete theme found: {cnt_obsolete_found}')
    if fix_old:
        log.info(f'Obsolete theme migrated: {cnt_obsolete_migrated}')
    elif cnt_obsolete_found:
        log.info(f'*** You may want to use the --fix-old argument to fix the pre-1.1.0 datasets')

def migrate_themes():
    # migrate current extras
    # CKAN >= 2.12: extras JSONB; il comando storico lavorava su record PackageExtra,
    # qui si itera sui Package e si usa pkg.extras['theme']
    extra_themes = Session.query(Package) \
        .filter(Package.extras['theme'].astext.like('%"subthemes"%'))

    cnt_extra = extra_themes.count()

    log.info(f'Migrating theme extra keys: {cnt_extra}')
    for pkg in extra_themes:
        # rinomina la chiave 'theme' -> FIELD_THEMES_AGGREGATE dentro il JSONB
        pkg.extras[FIELD_THEMES_AGGREGATE] = pkg.extras.pop('theme')
        Session.add(pkg)
    Session.commit()

    return cnt_extra

def check_obsolete_themes(fix_old):
    bad_extra_themes = Session.query(Package) \
            .filter(Package.extras['theme'].astext.notlike('%"subthemes"%'))

    cnt_bad = bad_extra_themes.count()
    migrated = 0

    if cnt_bad:
        log.error(f'There are {cnt_bad} themes in the 1.0.0 plain format. Please review your DB.')

        if fix_old:
            import ckanext.dcatapit.commands.migrate110 as migrate110

            uuid = [pkg.id for pkg in bad_extra_themes]
            log.debug(f'bad packages id {uuid}')
            migrated = migrate110.do_migrate_data(skip_orgs=True, pkg_uuid=uuid)

    return cnt_bad, migrated
