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

Non si scarica il codice sorgente e non si fa nessuna build: bastano due file,
il compose e la configurazione `.env`.

**1. Scaricare i due file**

```sh
mkdir ckan && cd ckan
curl -fsSLO https://raw.githubusercontent.com/piersoft/ckan-docker-ita-212/main/docker-compose.hub.yml
curl -fsSL  https://raw.githubusercontent.com/piersoft/ckan-docker-ita-212/main/.env.hub.example -o .env
```

Il secondo comando salva il modello di configurazione direttamente come `.env`.

**2. Modificare `.env` prima del primo avvio**

```sh
nano .env
```

Da cambiare subito:

- `CKAN_SITE_URL` — indirizzo pubblico del portale (es. `https://dati.miocomune.it`) e,
  con lo stesso valore, `CKANEXT__DCAT__BASE__URI`
- `CKAN_SYSADMIN_PASSWORD` e `CKAN_SYSADMIN_EMAIL`
- in produzione, le password del database (vedi *Modificare la configurazione*)

**3. Avviare**

```sh
docker compose -f docker-compose.hub.yml up -d
```

Le immagini vengono scaricate da Docker Hub al primo `up`.

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

## Dopo il primo avvio

Da amministratore, in **Amministrazione → Configurazione** (`/ckan-admin/config`),
compilare i dati del catalogo: titolo, editore (nome e codice IPA) e descrizione.
Finché restano vuoti, `catalog.ttl` espone un editore senza nome né identificativo
e il catalogo non supera la validazione DCAT-AP_IT.

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
| `CKAN__HARVEST__JOB_ALL_ORDER` | Ordine in cui l'harvest di tutte le sorgenti (`ckan harvester job-all`) avvia i job: `created_desc` (default, sorgente più recente per prima), `created_asc`, `title_asc` (alfabetico A-Z), `title_desc` (Z-A). |
| `CKAN_OAIPMH_ADMIN_EMAIL` | Email nella risposta OAI-PMH Identify (default: email del sysadmin) |
| `CKANEXT__DCATITA__ACCESSIBILITY_STATEMENT_URL` | URL della dichiarazione di accessibilità (per le PA è obbligatoria, Linee guida AgID: quella pubblicata su form.agid.gov.it). Se valorizzato, il footer mostra il link «Dichiarazione di accessibilità»; vuoto (default) = nessun link. |
| `CKANEXT__DCATITA__FOOTER_REBUILT_BY` | Nome mostrato nel footer dopo «rebuilt by» (es. il fornitore che gestisce l'istanza). Vuoto (default) = `AgID`. |
| `CKAN_CUSTOM_CSS_DEFAULT` / `CKAN_CUSTOM_CSS_FORCE` | Tema predefinito accessibile (WCAG 2.1 AA) in `ckan/css.example`: con `true` (default) all'avvio viene impostato come «Custom CSS» (Admin → Config) se l'admin non ne ha uno proprio, e aggiornato alle nuove versioni finché l'admin non lo modifica (script `docker-entrypoint.d/04_custom_css.sh`). `false` non tocca mai il Custom CSS. `CKAN_CUSTOM_CSS_FORCE=true` lo sovrascrive col predefinito al prossimo avvio. Per tornare al predefinito basta anche svuotare il Custom CSS dall'admin e riavviare. |
| `POSTGRES_PASSWORD`, `CKAN_DB_PASSWORD`, `DATASTORE_READONLY_PASSWORD` | Password del database: in produzione cambiarle e riportarle negli URL `CKAN_SQLALCHEMY_URL` e `CKAN_DATASTORE_*_URL` **prima** del primo avvio |

## Modificare la configurazione

La configurazione sta solo nel file `.env` della cartella di installazione: non serve
mai una build. Dopo ogni modifica:

```sh
docker compose -f docker-compose.hub.yml up -d
```

Compose ricrea solo i container interessati (`restart` non basta: tiene il vecchio ambiente).

**Modificabili in qualsiasi momento**

- `CKAN_SITE_URL` / `CKANEXT__DCAT__BASE__URI` — rilette a ogni avvio. Cambiano anche le
  URI dei dataset nel catalogo: conviene fissarle prima che il catalogo venga harvestato.
- `CKAN__PLUGINS`, `CKANEXT__DCAT__RDF__PROFILES`, `CKAN_OAIPMH_ADMIN_EMAIL`, impostazioni
  di Xloader, SMTP, GeoNames, log e uWSGI.
- `NGINX_PORT_HOST` / `NGINX_SSLPORT_HOST`.
- `CKAN_ITA_TAG` — dopo la modifica: `pull` e `up -d` (vedi *Aggiornare*).

**Usate solo al primo avvio** (da decidere prima)

- Password del database (`POSTGRES_PASSWORD`, `CKAN_DB_PASSWORD`,
  `DATASTORE_READONLY_PASSWORD` e gli URL `CKAN_SQLALCHEMY_URL`, `CKAN_DATASTORE_*_URL`):
  PostgreSQL le applica solo quando crea il volume vuoto. Cambiarle dopo nel `.env`
  impedisce a CKAN di connettersi, a meno di cambiarle anche nel database.
- `CKAN_SYSADMIN_PASSWORD` — serve solo a creare l'utente; poi la password si cambia
  dal profilo utente nell'interfaccia.
- `CKAN_SETUP_GROUPS` — i gruppi tematici si creano una volta sola.
- Segreti applicativi — generati al primo avvio e conservati nel volume `ckan_storage`.
  Impostarli dopo nel `.env` invalida i token API già emessi.

Per ripartire da zero con una nuova configurazione (cancella tutti i dati):
`docker compose -f docker-compose.hub.yml down -v`, poi `up -d`.

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

I dati restano nei volumi `ckan_storage`, `pg_data` e `solr_data`, compresi i
gruppi tematici. Il container ricreato rigenera pero' `ckan.ini`: per rimettere le
impostazioni della mappatura tema→gruppo eseguire, a CKAN avviato,

```sh
docker compose -f docker-compose.hub.yml exec ckan bash /srv/app/setup_groups.sh
docker compose -f docker-compose.hub.yml restart ckan
```

(i gruppi esistenti vengono saltati).

## Sorgenti e licenza

Sorgenti, documentazione completa e CHANGELOG: <https://github.com/piersoft/ckan-docker-ita-212>.

Licenza GNU AGPL-3.0-or-later, come CKAN e le estensioni da cui deriva.
