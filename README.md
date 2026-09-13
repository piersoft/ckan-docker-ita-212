# CKAN Docker per l'Italia (DEMO)

> [!NOTE]
> Stack CKAN **2.12** + PostgreSQL **16** + Solr **9** + Redis + NGINX, già
> predisposto per le funzionalità open data italiane. Pensato per essere
> provato in locale e poi spostato su un dominio reale cambiando una sola
> variabile (`CKAN_SITE_URL`). Leggere il [CHANGELOG](CHANGELOG.md) per i
> passaggi più delicati legati all'harvesting dei cataloghi federati.

## Cosa include

- **CKAN 2.12.0** (Python 3.14, SQLAlchemy 2) sull'immagine ufficiale `ckan/ckan-base`.
- **DCAT-AP_IT** — `ckan/ckanext-dcatapit` (fork Geosolutions, adeguato a 2.12): form,
  vocabolari, profilo RDF `it_dcat_ap`.
- **Linked Open Data / DCAT-AP 3** — `ckanext-dcat` **2.4.4** upstream (4 patch minime in
  `ckan/patches/ckanext-dcat-patches/`) con export `catalog.rdf` / `catalog.ttl`,
  `/dataset/{id}.rdf|.ttl|.jsonld`.
- **`ckan/ckanext-dcatita`** — regole dati.gov.it (normalizzazione dei cataloghi federati,
  URI dei subcatalog, rifinitura del grafo) via interfacce ufficiali di ckanext-dcat;
  mappe per ente in `subcatalogs.json`.
- **Harvesting** — `ckanext-harvest` **1.6.3** upstream + 2 patch (`ckan/patches/ckanext-harvest-patches/`).
- **OAI-PMH** — `ckan/ckanext-oai-pmh-server` (DataCite/OpenAIRE).
- **MQA / data.europa.eu** — `ckan/ckanext-dcat-ap-edp-mqa` (facoltativo).
- **Multilingua** (`ckan/ckanext-multilang`) e **Xloader 2.5** per il DataStore.

Catena dei profili RDF: `dcat_ap_edp_mqa it_dcat_ap dcat_ita` (o `euro_dcat_ap_3 it_dcat_ap dcat_ita`
senza MQA). `dcat_ita` va sempre per ultimo.

I worker (jobs/xloader, harvest gather e fetch) girano come servizi Compose separati
(`ckan-worker`, `ckan-gather`, `ckan-fetch`) con la stessa immagine di `ckan`.

## Prerequisiti

- Docker Engine + plugin Compose v2 (comando `docker compose`).
  Guida: <https://docs.docker.com/engine/install/ubuntu/>
- Verifica: `docker run hello-world` e `docker compose version`.

---

## Configurazione (`.env`)

Tutta la configurazione passa dal file `.env`. Si parte da `.env.example`:
tutte le variabili hanno default sensati per un test locale, e l'unico blocco
realmente da toccare è quello in cima al file (`>>> DA MODIFICARE <<<`).

Variabili chiave:

| Variabile | A cosa serve |
|---|---|
| `CKAN_SITE_URL` | URL pubblico del portale, **senza slash finale**. Da qui vengono derivati automaticamente `ckanext.dcat.base_uri` e l'URL base OAI-PMH. |
| `CKAN_SYSADMIN_NAME` / `CKAN_SYSADMIN_PASSWORD` | Utente e password del primo amministratore. |
| `NGINX_PORT_HOST` / `NGINX_SSLPORT_HOST` | Porte host per accesso **non-SSL** e **SSL**. |
| `GEONAMES_USERNAME` | Username GeoNames per il geocoding (default `demo`). |
| `CKAN_OAIPMH_BASE_URL` | (opzionale) forza l'URL base OAI; se vuoto usa `${CKAN_SITE_URL}/oai`. |
| `CKAN__PLUGINS` | Plugin attivi. Facoltativi: `dcat_ap_edp_mqa` (profilo MQA), `oai_pmh_server` (OpenAIRE). Cambiarli richiede `docker compose up -d ckan` (ricrea il container), non basta `restart`. |
| `CKANEXT__DCAT__RDF__PROFILES` | Catena dei profili RDF: `dcat_ap_edp_mqa it_dcat_ap dcat_ita` (o `euro_dcat_ap_3 it_dcat_ap dcat_ita` senza MQA). `dcat_ita` sempre per ultimo. |
| `CKANEXT__DCATITA__MQA_BADGE` | `true` mostra nella pagina di ogni dataset il riquadro "Punteggio qualità dal portale europeo" letto via API da data.europa.eu (default `false`). Ha senso solo se il catalogo è harvestato dal portale europeo; per gli altri il riquadro resta senza punteggio. |
| `CKANEXT__DCATITA__HARVEST_VERIFY_SSL` | `false` (default) non verifica i certificati TLS dei cataloghi harvestati via RDF. |
| `CKANEXT__OAI_PMH_SERVER__RESUMPTION_TOKEN_BATCH_SIZE` | Record per pagina di `ListRecords` (default `1024`). |
| `CKAN_LOG_LEVEL_EXTENSIONS` | Livello di log delle estensioni (default `INFO`; `DEBUG` è molto verboso). |

> Le variabili `CKAN___*` / `CKANEXT__*` sono lette dal plugin `envvars` e finiscono in
> `ckan.ini` (`CKANEXT__DCATITA__MQA_BADGE` → `ckanext.dcatita.mqa_badge`).

### Demo locale vs dominio reale

Basta impostare `CKAN_SITE_URL` 

- HTTP locale: `CKAN_SITE_URL=http://localhost:8090`
- HTTPS locale: `CKAN_SITE_URL=https://localhost:8453`
- IP privato: `CKAN_SITE_URL=http://192.168.1.50:8080`
- Produzione: `CKAN_SITE_URL=https://dati.miocomune.it`

### SSL o non-SSL

NGINX espone **entrambi** gli accessi contemporaneamente:

- non-SSL → `http://<host>:${NGINX_PORT_HOST}` (default `8090`)
- SSL → `https://<host>:${NGINX_SSLPORT_HOST}` (default `8453`, certificato
  self-signed generato in automatico al primo avvio).

Si usa quello che si preferisce; `CKAN_SITE_URL` deve coerentemente puntare
allo schema/porta scelti. In produzione vedi la sezione *Produzione* (Let's Encrypt).

---

## Primo avvio (passi esatti)

Eseguire i comandi **in ordine**, aspettando il completamento di ciascuno.

1. Clonare e preparare il `.env`:

   ```sh
   git clone https://github.com/piersoft/ckan-docker-ita-212.git
   cd ckan-docker-ita-212
   cp .env.example .env
   ```

2. Modificare nel `.env` almeno `CKAN_SITE_URL` e `CKAN_SYSADMIN_PASSWORD`
   (vedi tabella sopra).

3. Costruire le immagini:

   ```sh
   docker compose build
   ```

4. Avviare lo stack:

   ```sh
   docker compose up -d
   ```

5. Attendere che CKAN sia **healthy** (il primo avvio carica i vocabolari
   DCAT-AP_IT e può richiedere alcuni minuti):

   ```sh
   docker compose ps
   ```

6. Eseguire **una sola volta** il setup dei gruppi tematici (idempotente):

   ```sh
   docker compose exec ckan bash /srv/app/setup_groups.sh
   ```

Il portale è ora raggiungibile all'indirizzo impostato in `CKAN_SITE_URL`.

> [!NOTE]
> L'init una tantum (tabelle e vocabolari DCAT-AP_IT) è protetto da un marker nel
> volume `ckan_storage` e da un controllo sul DB: un `docker compose build` o
> `up --build` successivo **non** lo riesegue. `ckan.ini` vive nel container e viene
> rigenerato a ogni rebuild dagli script in `ckan/docker-entrypoint.d/`.

---

## Comandi utili

- **Build** (ricostruire le immagini):

  ```sh
  docker compose build
  ```

- **Start / Stop**:

  ```sh
  docker compose up -d
  docker compose down          # ferma e rimuove i container (i volumi restano)
  ```

- **Dopo una modifica al `.env`** (plugin, profili, `EXTRA_UWSGI_OPTS`, badge MQA…):
  va ricreato il container, non l'immagine. `restart` non basta (tiene l'ambiente vecchio).

  ```sh
  docker compose up -d ckan && docker compose up -d
  ```
  (il secondo `up` riallinea i worker, che leggono lo stesso `.env`)

- **Dopo una modifica al codice** (estensioni in `ckan/`, patch, script di init, Dockerfile):
  va ricostruita l'immagine.

  ```sh
  docker compose up -d --build ckan && docker compose up -d
  ```
  (NGINX ri-risolve l'upstream da solo, non serve riavviarlo)

- **Reindex Solr** (es. dopo un restore del DB):

  ```sh
  docker compose exec ckan ckan search-index rebuild -e
  ```

- **Setup iniziale dei gruppi** (vedi passo 6):

  ```sh
  docker compose exec ckan bash /srv/app/setup_groups.sh
  ```

- **Log** in tempo reale:

  ```sh
  docker compose logs -f ckan
  ```

- **Reset totale** (cancella anche i dati: DB, indice Solr, storage):

  ```sh
  docker compose down -v
  ```

---

## Manutenzione periodica (cron)

`scripts/maintenance.sh` raccoglie i lavori ricorrenti; `scripts/crontab.example` è il
crontab consigliato per root (adattare il percorso):

| quando | comando | cosa fa |
|---|---|---|
| ogni 15 min | `harvest-run` | `ckan harvester run`: avvia i job delle sorgenti la cui frequenza (`DAILY`, `WEEKLY`…) è scaduta **e chiude quelli finiti** (senza, restano "Running"). Con sorgenti `MANUAL` non crea job. |
| ogni notte | `harvest-all` | `ckan harvester job-all` + `run`: harvest di **tutte** le sorgenti attive, indipendentemente dalla frequenza |
| ogni notte | `daily` | `abort-failed-jobs` (job harvest in limbo), `clean-harvest-log`, `xloader-cleanup`, pulizia log/job xloader >30 gg, `docker image prune` |
| domenica | `weekly` | build cache Docker >7 gg, container fermi, riepilogo `docker system df` |
| dentro `daily` | `xloader-cleanup` | marca "error" i job xloader rimasti `pending`/`running` da oltre 6 ore (container riavviato, worker ucciso): senza, quella risorsa non viene più risottomessa |
| ogni notte (dopo l'harvest) | `xloader-refresh` | `ckan xloader submit all-existing`: ricarica nel DataStore le risorse già caricate. **Serve sui cataloghi harvestati**: se l'URL della risorsa è persistente (un webservice che espone sempre lo stesso `dati.csv`) il contenuto cambia senza che cambino i metadati, quindi l'harvest non tocca il dataset, gli hook di xloader non scattano e l'anteprima del DataStore resta obsoleta. Pesante (riscarica ogni file): settimanale se i dati cambiano di rado. |

I log dei container sono ruotati da Docker (`x-logging` in `docker-compose.yml`: 20 MB × 3
per servizio); il log della manutenzione va in `/var/log/ckan212-maintenance.log`
(`scripts/logrotate.conf` → `/etc/logrotate.d/`).

## Verifica delle funzionalità

- Catalogo RDF: `${CKAN_SITE_URL}/catalog.rdf` e `.../catalog.ttl`
- RDF del singolo dataset: `${CKAN_SITE_URL}/dataset/{id}.rdf`
- OAI-PMH: `${CKAN_SITE_URL}/oai?verb=Identify`,
  `.../oai?verb=ListMetadataFormats`,
  `.../oai?verb=ListRecords&metadataPrefix=oai_dc`
- Harvesting: interfaccia in `${CKAN_SITE_URL}/harvest`

---

## Produzione (dominio reale + Let's Encrypt)

Il certificato resta gestito da certbot **sull'host** (`/etc/letsencrypt`); NGINX lo
monta in sola lettura tramite l'override `docker-compose.prod.yml`:

```sh
cp nginx/prod/default.conf.example nginx/prod/default.conf
sed -i 's/DOMINIO/dati.miocomune.it/g' nginx/prod/default.conf
# nel .env:
#   CKAN_SITE_URL=https://dati.miocomune.it
#   CKANEXT__DCAT__BASE__URI=https://dati.miocomune.it
#   NGINX_PORT_HOST=80   NGINX_SSLPORT_HOST=443
#   COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker compose up -d
```

La porta 80 fa solo redirect a HTTPS (le challenge ACME non servono se certbot usa
un authenticator DNS). Dopo ogni rinnovo del certificato:
`docker compose exec nginx nginx -s reload` (es. come `--deploy-hook` di certbot).

## Migrare da ckan-docker-ita (CKAN 2.10)

Procedura collaudata su un catalogo reale (10.437 dataset, 314k extras, 930 MB), con i
due stack che convivono sulla stessa macchina (`COMPOSE_PROJECT_NAME`, nomi container e
porte diversi). Il vecchio stack **non viene modificato**: solo `pg_dump` in lettura.

1. Avviare il nuovo stack vuoto (init: tabelle e vocabolari) e verificarlo.
2. Dump dal vecchio DB e restore nel nuovo (il restore parallelo vuole un file, non stdin):

   ```sh
   docker exec db pg_dump -U postgres -Fc ckandb > ckandb.dump
   docker exec db pg_dump -U postgres -Fc datastore > datastore.dump
   docker compose stop ckan ckan-worker ckan-gather ckan-fetch
   docker compose exec -T db psql -U postgres -c "DROP DATABASE ckandb" -c "CREATE DATABASE ckandb OWNER ckandbuser" \
       -c "DROP DATABASE datastore" -c "CREATE DATABASE datastore OWNER ckandbuser"
   docker cp ckandb.dump db212:/tmp/ && docker cp datastore.dump db212:/tmp/
   docker compose exec -T db pg_restore -U postgres -d ckandb --no-owner --role=ckandbuser --no-privileges -j 4 /tmp/ckandb.dump
   docker compose exec -T db pg_restore -U postgres -d datastore --no-owner --role=ckandbuser --no-privileges -j 4 /tmp/datastore.dump
   ```

3. `docker compose up -d`: `prerun.py` esegue `ckan db upgrade` (schema 2.10 → 2.12:
   extras in JSONB, `package_extra` rimossa, migrazioni dei plugin), poi
   `ckan datastore set-permissions`. Verifica: `select version_num from alembic_version`
   → `9445ce34fc23`.
4. Reindex Solr (~1,5 ore per 10k dataset, in background):

   ```sh
   docker compose exec -d ckan sh -c "ckan search-index rebuild -e > /var/lib/ckan/reindex.log 2>&1"
   ```

5. Copiare i file caricati dal vecchio volume `ckan_storage` (`storage/ e /resources`) nel nuovo,
   con owner `503:502` (utente `ckan`).
6. Confrontare `dataset.ttl` e `catalog.ttl` fra i due stack (stessi predicati, stesse URI).
7. Switch: `docker compose stop` sul vecchio stack, `.env` di produzione (sezione sopra),
   `docker compose up -d --force-recreate ckan ckan-worker ckan-gather ckan-fetch nginx`.
   Rollback: fermare nginx/ckan nuovi e `docker compose start` sul vecchio.

## Note sulle regole per l'harvesting dei cataloghi federati

Le regole nate dall'analisi degli harvesting dei cataloghi nazionali, regionali e
comunali su [dati.gov.it](https://dati.gov.it) (metadati incompleti o non conformi
dei cataloghi remoti) non sono più patch a `ckanext-dcat` ma vivono in
[`ckan/ckanext-dcatita`](ckan/ckanext-dcatita/README.md): plugin `dcatita_harvest`
(normalizzazione), `dcatita_uri` (URI dei subcatalog) e profilo `dcat_ita`. Le
mappe per ente stanno in `subcatalogs.json`. Per un'installazione **stand-alone**
(senza harvesting di cataloghi terzi) si possono lasciare attivi: non incidono.

## Disattivare l'integrazione OpenAIRE / MQA

1. rimuovere `dcat_ap_edp_mqa` e/o `oai_pmh_server` da `CKAN__PLUGINS` nel `.env`;
2. impostare `CKANEXT__DCAT__RDF__PROFILES=euro_dcat_ap_3 it_dcat_ap dcat_ita`.

## Licenza

Il repository e `ckan/ckanext-dcatita` sono rilasciati sotto **GNU AGPL-3.0-or-later**
(la stessa di CKAN, ckanext-dcat, ckanext-harvest, ckanext-dcatapit e ckanext-multilang,
di cui questo repository contiene fork che ne conservano la licenza).
`ckan/ckanext-oai-pmh-server` e `ckan/ckanext-dcat-ap-edp-mqa` restano LGPL-3.0
(vedi i rispettivi `LICENSE`).

## Crediti

- Estensione DCAT-AP_IT: [Geosolutions — ckanext-dcatapit](https://github.com/geosolutions-it/ckanext-dcatapit)
- Multilingua: [Geosolutions — ckanext-multilang](https://github.com/geosolutions-it/ckanext-multilang)
- DCAT: [ckan/ckanext-dcat](https://github.com/ckan/ckanext-dcat), harvest: [ckan/ckanext-harvest](https://github.com/ckan/ckanext-harvest)
- MQA: [tlmat-unican — ckanext-dcat-ap-edp-mqa](https://github.com/tlmat-unican/ckanext-dcat-ap-edp-mqa)
- OAI-PMH: [tlmat-unican — ckanext-oai-pmh-server](https://github.com/tlmat-unican/ckanext-oai-pmh-server)
- Immagini base CKAN: [ckan/ckan-docker-base](https://github.com/ckan/ckan-docker-base)

- Progetto e personalizzazione a cura di @piersoft (Francesco Piero Paolicelli)
