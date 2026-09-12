"""
Autocomplete dei vocabolari DCAT-AP_IT (regioni, temi EU, luoghi, lingue) usato
dai campi del form dataset (vedi `data_module_source` in schema.py):

    /api/2/util/vocabulary/autocomplete?vocabulary_id=<voc>&incomplete=<q>

Riscritto per Flask/CKAN 2.12: la vecchia versione usava request.str_params,
urllib.unquote e la rotta Pylons (IRoutes) che non esiste piu'.
"""
import logging
from urllib.parse import unquote

from flask import Blueprint, jsonify

import ckan.model as model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


def vocabulary_autocomplete():
    q = unquote(tk.request.args.get('incomplete', '') or '')
    vocab = tk.request.args.get('vocabulary_id')
    limit = tk.request.args.get('limit', 10)

    tag_names = []
    if q and vocab:
        context = {'model': model, 'session': model.Session,
                   'user': tk.g.user, 'auth_user_obj': tk.g.userobj}
        data_dict = {'q': q, 'limit': limit, 'vocabulary_id': vocab}
        try:
            tag_names = tk.get_action('tag_autocomplete')(context, data_dict)
        except tk.ObjectNotFound:
            log.warning('Vocabolario %s non trovato', vocab)

    return jsonify({'ResultSet': {'Result': [{'Name': t} for t in tag_names]}})


def get_blueprint():
    bp = Blueprint('dcatapit_api', __name__)
    for rule in ('/api/util/vocabulary/autocomplete',
                 '/api/1/util/vocabulary/autocomplete',
                 '/api/2/util/vocabulary/autocomplete',
                 '/api/3/util/vocabulary/autocomplete'):
        bp.add_url_rule(rule, view_func=vocabulary_autocomplete, methods=['GET'])
    return bp
