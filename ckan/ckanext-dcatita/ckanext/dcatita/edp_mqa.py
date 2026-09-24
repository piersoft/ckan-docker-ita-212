# -*- coding: utf-8 -*-
"""
Punteggio MQA (Metadata Quality Assessment) di data.europa.eu per un dataset CKAN.

Metodologia MQA v2 (set. 2026): scala 0-7,5
  Sufficiente < 2,5 | Buono 2,5-5 | Eccellente >= 5

Il valore mostrato e' "datasetFinal" (l'"Agregated rating" della pagina qualita'
di data.europa.eu), letto da /api/mqa/cache/datasets/{id}. Quell'API rifiuta le
chiamate dal browser (HTTP 500 con header Origin diverso da data.europa.eu),
quindi il calcolo avviene qui, lato server, durante il rendering della pagina.

Flusso:
  1. search API (q="<identifier>") per risolvere l'ID EDP del dataset
  2. API MQA v2 per leggere datasetFinal (o "No v2 metrics found" = non rivalutato)
  3. risultato in cache Redis (successo 6 ore, esito negativo 30 minuti)
  4. se data.europa.eu non risponde, si sospendono le chiamate per 5 minuti
     (circuit breaker) per non rallentare le pagine

Uso nei template:  {% set mqa = h.dcatita_edp_mqa(pkg) %}
"""

import json
import logging
import re
import unicodedata

import requests

log = logging.getLogger(__name__)

SEARCH_URL = 'https://data.europa.eu/api/hub/search/search'
MQA_URL = 'https://data.europa.eu/api/mqa/cache/datasets/'
EDP_PAGE = 'https://data.europa.eu/data/datasets/'
EDP_HOME = 'https://data.europa.eu/data/datasets?locale=it'

TIMEOUT = (3, 5)            # (connessione, lettura) in secondi
CACHE_TTL_OK = 6 * 3600     # esito con punteggio o "in attesa di rivalutazione"
CACHE_TTL_KO = 30 * 60      # dataset non trovato / errore
BREAKER_TTL = 5 * 60        # pausa dopo un errore di rete verso data.europa.eu
KEY_PREFIX = 'dcatita:edp_mqa:v2:'
BREAKER_KEY = 'dcatita:edp_mqa:breaker'

HEADERS = {'Accept': 'application/json', 'User-Agent': 'CKAN dcatita edp_mqa'}


# ------------------------------------------------------------------ redis

def _redis():
    try:
        from ckan.lib.redis import connect_to_redis
        return connect_to_redis()
    except Exception:
        return None


def _cache_get(key):
    r = _redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _cache_set(key, value, ttl):
    r = _redis()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass


# ------------------------------------------------------------------ id EDP

def _normalize(s):
    """Stessa normalizzazione del JS CKAN e del blocco Drupal:
    lower, niente diacritici, solo ':' e '.' -> '-', underscore intatti."""
    s = (s or '').strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace(':', '-').replace('.', '-')
    for q in (u'\u2019', u'\u2018', u'\u00b4', '`'):
        s = s.replace(q, "'")
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def _edp_id_from_resource(resource):
    rid = re.sub(r'[?#].*$', '', resource or '')
    return re.sub(r'^.*/dataset/', '', rid)


def _candidates(pkg):
    raw = (pkg.get('identifier') or '').strip()
    if not raw:
        for e in pkg.get('extras') or []:
            if e.get('key') == 'identifier':
                raw = (e.get('value') or '').strip()
                break
    cands = []
    for c in (_normalize(raw), raw, raw.lower()):
        if c and c != 'none' and c not in cands:
            cands.append(c)
    return cands


def _resolve_edp_id(cands):
    """Ritorna l'ID EDP (con eventuale ~~N) coerente con uno dei candidati."""
    expected = set(cands)
    for cand in cands:
        params = {
            'filters': 'dataset',
            'q': '"%s"' % cand,
            'limit': 20,
            'includes': 'id,resource,quality_meas',
        }
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        results = (resp.json().get('result') or {}).get('results') or []

        best_id, best_score, first_id = None, None, None
        for r in results:
            rid = _edp_id_from_resource(r.get('resource'))
            if not rid:
                continue
            base = re.sub(r'~~\d+$', '', rid)
            if rid not in expected and base not in expected:
                continue
            if first_id is None:
                first_id = rid
            sc = (r.get('quality_meas') or {}).get('scoring')
            if sc is not None and (best_score is None or sc > best_score):
                best_id, best_score = rid, sc
        found = best_id or first_id
        if found:
            return found
    return None


# ------------------------------------------------------------------ punteggio

def _band(score):
    if score >= 5:
        return 'Eccellente', 'green'
    if score >= 2.5:
        return 'Buono', 'goldenrod'
    return 'Sufficiente', 'red'


def _result(status, edp_id=None, score=None):
    out = {
        'status': status,   # ok | pending | notfound | error
        'score': score,
        'score_fmt': None,
        'label': None,
        'color': None,
        'link': (EDP_PAGE + requests.utils.quote(edp_id, safe='') + '/quality?locale=it')
                if edp_id else EDP_HOME,
    }
    if status == 'ok' and score is not None:
        out['score_fmt'] = ('%.1f' % score).replace('.', ',') + ' / 7,5'
        out['label'], out['color'] = _band(score)
    return out


def edp_mqa(pkg):
    """Helper di template: dict con status, score_fmt, label, color, link."""
    if not isinstance(pkg, dict) or not pkg.get('id'):
        return _result('notfound')

    key = KEY_PREFIX + pkg['id']
    cached = _cache_get(key)
    if cached:
        return cached

    if _cache_get(BREAKER_KEY):
        return _result('error')

    cands = _candidates(pkg)
    if not cands:
        res = _result('notfound')
        _cache_set(key, res, CACHE_TTL_KO)
        return res

    try:
        edp_id = _resolve_edp_id(cands)
        if not edp_id:
            res = _result('notfound')
            _cache_set(key, res, CACHE_TTL_KO)
            return res

        resp = requests.get(MQA_URL + requests.utils.quote(edp_id, safe=''),
                            headers=HEADERS, timeout=TIMEOUT)
        try:
            data = resp.json()
        except ValueError:
            data = {}

        final = None
        results = (data.get('result') or {}).get('results') or []
        if results:
            final = results[0].get('datasetFinal')

        if isinstance(final, (int, float)):
            res = _result('ok', edp_id, float(final))
            ttl = CACHE_TTL_OK
        elif 'no v2 metrics' in str(data.get('message', '')).lower():
            res = _result('pending', edp_id)
            ttl = CACHE_TTL_OK
        else:
            res = _result('notfound', edp_id)
            ttl = CACHE_TTL_KO

        log.debug('EDP MQA %s -> %s (%s)', pkg.get('name'), res['status'], edp_id)
        _cache_set(key, res, ttl)
        return res

    except requests.RequestException as e:
        log.warning('EDP MQA non raggiungibile per %s: %s', pkg.get('name'), e)
        _cache_set(BREAKER_KEY, {'down': True}, BREAKER_TTL)
        return _result('error')
    except Exception as e:
        log.warning('EDP MQA errore per %s: %s', pkg.get('name'), e)
        return _result('error')
