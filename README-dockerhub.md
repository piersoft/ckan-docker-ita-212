# CKAN Docker per l'Italia — CKAN 2.12 + DCAT-AP_IT

Stack CKAN pronto all'uso per i cataloghi open data italiani: **CKAN 2.12**,
**DCAT-AP_IT** (form, vocabolari e profilo RDF), **DCAT-AP 3**, harvesting di
cataloghi federati, DataStore con Xloader, OAI-PMH e profilo MQA di data.europa.eu.

Non serve compilare nulla: le immagini sono già pronte su Docker Hub.

| Immagine | Contenuto |
|---|---|
| `piersoft/ckan` | CKAN 2.12 con estensioni dcat, dcatapit, dcatita, harvest, multilang, xloader, oai-pmh, MQA (usata anche dai worker) |
| `piersoft/ckan-solr` | Solr 9 con lo schema CKAN + campi DCAT-AP_IT già installati |
| `piersoft/ckan-db` | PostgreSQL 16 con la creazione automatica dei database CKAN e DataStore |
| `piersoft/ckan-nginx` | NGINX reverse proxy, HTTP e HTTPS (certificato self-signed generato al primo avvio) |

Redis usa l'immagine ufficiale `redis:7`.

## Tag

- `2.12-dcatapit-X.Y.Z` — versione fissa, consigliata in produzione
- `2.12` — ultima versione della serie 2.12
- `latest` — uguale a `2.12`

Le quattro immagini vanno usate sempre con lo stesso tag (variabile `CKAN_ITA_TAG`).

## Avvio rapido

Requisiti: Docker Engine con Compose v2 (`docker compose version`), architettura amd64.

```sh
mkdir ckan && cd ckan
curl -fsSLO https://raw.githubusercontent.com/piersoft/ckan-docker-ita-212/main/docker-compose.hub.yml
curl -fsSL  https://raw.githubusercontent.com/piersoft/ckan-docker-ita-212/main/.env.hub.example -o .env
# modificare nel .env almeno CKAN_SITE_URL e CKAN_SYSADMIN_PASSWORD
docker compose -f docker-compose.hub.yml up -d
```

Il primo avvio richiede alcuni minuti (creazione del database e caricamento dei
vocabolari DCAT-AP_IT). Lo stato si controlla con:

```sh
docker compose -f docker-compose.hub.yml ps
```

Quando `ckan` risulta **healthy**, il portale risponde su `CKAN_SITE_URL`
(default `http://localhost:8080`, oppure `https://localhost:8443`).
Accesso con l'utente `CKAN_SYSADMIN_NAME` e la password impostata nel `.env`.

Per non ripetere `-f` a ogni comando: aggiungere al `.env`
`COMPOSE_FILE=docker-compose.hub.yml`.

## Cosa avviene in automatico

- **Database e indice**: creazione dei database CKAN e DataStore, dello schema
  e dell'indice Solr con i campi DCAT-AP_IT.
- **Vocabolari DCAT-AP_IT**: temi, sottotemi EuroVoc, lingue, luoghi, frequenze,
  formati, licenze, regioni.
- **Gruppi tematici**: creati al primo avvio (`CKAN_SETUP_GROUPS=true`).
- **Segreti applicativi**: se non sono impostati nel `.env` vengono generati
  al primo avvio e conservati nel volume `ckan_storage`, quindi restano gli
  stessi tra un riavvio e l'altro.
- **URI del catalogo**: `ckanext.dcat.base_uri` e l'URL OAI-PMH derivano da
  `CKAN_SITE_URL`.

## Variabili principali (`.env`)

| Variabile | A cosa serve |
|---|---|
| `CKAN_SITE_URL` | URL pubblico del portale, senza slash finale |
| `CKAN_SYSADMIN_NAME` / `CKAN_SYSADMIN_PASSWORD` / `CKAN_SYSADMIN_EMAIL` | Primo amministratore |
| `NGINX_PORT_HOST` / `NGINX_SSLPORT_HOST` | Porte HTTP e HTTPS sull'host (default 8080 / 8443) |
| `CKAN_ITA_TAG` | Versione delle immagini (default `2.12`) |
| `CKAN_SETUP_GROUPS` | `true` crea i gruppi tematici al primo avvio |
| `CKAN__PLUGINS` | Plugin attivi; facoltativi `dcat_ap_edp_mqa` e `oai_pmh_server` |
| `CKANEXT__DCAT__RDF__PROFILES` | Catena dei profili RDF (`dcat_ita` sempre per ultimo) |
| `CKAN_OAIPMH_ADMIN_EMAIL` | Email nella risposta OAI-PMH Identify (default: email del sysadmin) |
| `POSTGRES_PASSWORD`, `CKAN_DB_PASSWORD`, `DATASTORE_READONLY_PASSWORD` | Password del database: in produzione cambiarle e riportarle negli URL `CKAN_SQLALCHEMY_URL` e `CKAN_DATASTORE_*_URL` **prima** del primo avvio |

Dopo una modifica al `.env` ricreare i container:
`docker compose -f docker-compose.hub.yml up -d`.

## Verifica

- Catalogo: `${CKAN_SITE_URL}/catalog.ttl` (anche `.rdf`, `.jsonld`)
- Singolo dataset: `${CKAN_SITE_URL}/dataset/{id}.ttl`
- OAI-PMH: `${CKAN_SITE_URL}/oai?verb=Identify`
- Harvesting: `${CKAN_SITE_URL}/harvest`

## Produzione con un certificato reale

L'immagine NGINX usa un certificato self-signed. Con un dominio reale si monta
una propria configurazione e i certificati dell'host (per esempio Let's Encrypt)
aggiungendo al servizio `nginx` di `docker-compose.hub.yml`:

```yaml
    volumes:
      - ./default.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
```

Un modello di `default.conf` è nel repository dei sorgenti (`nginx/prod/default.conf.example`).

## Aggiornare

```sh
# cambiare CKAN_ITA_TAG nel .env, poi
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

I dati restano nei volumi `ckan_storage`, `pg_data` e `solr_data`.

## Sorgenti e licenza

Sorgenti, documentazione completa e CHANGELOG: <https://github.com/piersoft/ckan-docker-ita-212>.

Licenza GNU AGPL-3.0-or-later, come CKAN e le estensioni da cui deriva.
