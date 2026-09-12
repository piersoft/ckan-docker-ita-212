# Changelog

## `2026-09-12` — Pulizia dei residui 2.10
- Rimossi dalla repo `ckan/Dockerfile.legacy-2.10` e i file di `ckan/patches` non piu' usati (copie intere di moduli CKAN/Pylons: `base.py`, `core.py`, `xmlrpc.py`, `jsonrpc.py`, `supervisord.conf`, `command.py`, `model_dictize.py`, `validators.py`, `util.py`, template ecc.). Restano nella history.
- Le due patch core ancora necessarie sono riportate come `.patch` contro CKAN 2.12.0 in `ckan/patches/ckan-core-patches/`: selettore lingua con campo `redirect_url` (un campo `url` nel form dataset sovrascriveva l'extra `landingpage`). La patch `resource_id_validator` min 5 non serve piu': il validator non esiste in 2.12.
- **Attenzione (CKAN >= 2.11)**: gli `id` di risorse devono essere UUID v4. La patch al CKAN harvester (`03_ckanharvester.patch`) non allunga piu' gli id corti con cifre casuali (oggi invalidi) ma rimuove gli id non-UUID lasciandoli generare a CKAN. Gli id dei dataset remoti restano ammessi (schema sostituito dall'harvester).

## `2026-09-12` — Post-switch: landingPage in subcatalogs.json, cache organizzazioni, log
- Le ~200 righe di mapping `holder_identifier -> landingPage` di `dcatapit/dcat/profiles.py` (e la riscrittura per ente delle URI delle distribuzioni, ormai doppia) sono sostituite da `rules.landing_page()` di ckanext-dcatita, guidata dalla chiave `landing` di `subcatalogs.json` (45 voci). Unico posto per le regole per ente.
- `organization_show` in dcatapit (indicizzazione, `package_search`, profilo RDF) passa da una cache per processo con TTL 120 s, invalidata alla modifica di un'organizzazione: `catalog.ttl` non interroga piu' il DB per l'organizzazione di ogni dataset.
- Log delle estensioni a INFO (`CKAN_LOG_LEVEL_EXTENSIONS`, default INFO): multilang a DEBUG scriveva centinaia di righe per pagina di catalogo.
- Profilo `dcat_ap_edp_mqa`: i cicli su spatial/language/accessRights/theme/format scorrevano l'intero grafo a ogni dataset (O(n²): 44 s su 64 per una pagina di 100 dataset); ora limitati al dataset corrente e alle sue distribuzioni. Cache del vocabolario licenze in dcatapit (2.500+ query per pagina). Risultato: `catalog.ttl` **10-12 s/pagina** contro 25-30 prima e ~18 s del 2.10.
- certbot: deploy hook in `/etc/letsencrypt/renewal-hooks/deploy/` che ricarica NGINX del nuovo stack; `certbot renew --dry-run` OK per il certificato del catalogo.

## `2026-09-12` — Fase 6: migrazione del catalogo reale e switch in produzione
- Restore del DB del 2.10 (10.437 dataset, 8 harvest source, 204k risorse, 314k extras, 44k righe multilang) nel nuovo stack: `ckan db upgrade` porta lo schema a `9445ce34fc23` (2.12), converte gli extras in JSONB e rimuove `package_extra`; le migrazioni Alembic di harvest/dcatapit/multilang sono compatibili (solo `DROP ... IF EXISTS`).
- Reindex Solr di 10.437 dataset senza errori (~1,6 dataset/s con dcatapit + multilang).
- Confronto `dataset.ttl` 2.10 vs 2.12: stesse URI, identificatori, landingPage e cardinalita' dei predicati. Differenze volute: date solo-giorno come `xsd:date`, `dcat:byteSize` come `xsd:nonNegativeInteger` (DCAT-AP 3), landingPage tipizzata `foaf:Document`, downloadURL `rdfs:Resource`, nessun nodo `vcard:Organization` orfano.
- Fix emersi sul catalogo reale: `before_dataset_index` senza `theme`, `organization_show` mancante in `package_search`, `Group._extras` in multilang `group_list`, byteSize decimal che rompeva il profilo DCAT-AP 3 sulle pagine del catalogo, `UnknownIPR` ridondante sulle licenze, nodo distribuzione sdoppiato (`resource_uri()` ora riscritto per tutti i profili via cache dataset→subcatalog), `//` nella landingPage di dcatapit.
- Produzione: `docker-compose.prod.yml` + `nginx/prod/default.conf` (Let's Encrypt dell'host, redirect 80→443). Switch di ckan.piersoftckan.biz dal 2.10 al 2.12 con il vecchio stack fermato ma intatto (rollback = `docker compose start`).
- Tempi di `catalog.ttl`: ~20-27 s/pagina contro ~18 s del 2.10 (ereditati: `organization_show` per dataset in dcatapit e log DEBUG multilang) — ottimizzazione in una fase successiva.
- Dichiarate le opzioni di configurazione di dcatapit e dcatita (`config_declaration.yaml`): niente piu' warning "Option ... is not declared".

## `2026-09-12` — Fase 5: OAI-PMH server e profilo MQA
- `ckan/ckanext-oai-pmh-server`: `iteritems`->`items`; `pyoai` patchato a build time (`patches/patch_pyoai.py`) perche' importa `pkg_resources`, assente con i setuptools recenti. Configurazione OAI riapplicata a ogni avvio (idempotente), token xloader ricreato quando manca in `ckan.ini`.
- `ckan/ckanext-dcat-ap-edp-mqa`: il profilo `dcat_ap_edp_mqa` ora estende `EuropeanDCATAP3Profile` e va usato **al posto** di `euro_dcat_ap_3` (`dcat_ap_edp_mqa it_dcat_ap dcat_ita`); cache dei vocabolari EDP nel volume `ckan_storage` con fallback ai file bundled (il nome file upstream conteneva una virgoletta tipografica).
- `dcat_ita`: potatura dei nodi-licenza orfani (`dct:type adms:licencetype/UnknownIPR`) lasciati dal profilo EU quando `it_dcat_ap` sostituisce `dct:license`.
- Init: `initdb`/`load` dei vocabolari dcatapit saltati se `dcatapit_vocabulary` e' gia' popolata (controllo sul DB).

## `2026-09-12` — Fase 4: ckanext-dcatapit e ckanext-multilang su CKAN 2.12
- `ckan/ckanext-dcatapit` (fork con le fix DGA/licenze in `profiles.py`) adeguato a CKAN 2.12 / Python 3.14 / SQLAlchemy 2: extras JSONB al posto di `PackageExtra`/`GroupExtra`, `IGroupForm` con `create/update/show_group_schema()`, CSRF nel form thesaurus, import senza Pylons/routes, `map_imperatively` e `has_table` nei modelli, `ConfigParser.read_file`, regex raw, migrazione Alembic tollerante all'ordine con `initdb`, guardie su `holder_identifier`/`frequency`/multilang assenti.
- Autocomplete dei vocabolari (`/api/2/util/vocabulary/autocomplete`) riscritto come blueprint Flask: sul 2.10 la rotta Pylons era gia' morta.
- `ckan/ckanext-multilang` vendorizzato da geosolutions-it (master 2026-05) e portato a SQLAlchemy 2; va caricato **prima** di `dcatapit_pkg`.
- Init una tantum (vocabolari, tabelle) protetto da un marker nel volume `ckan_storage` invece che in `ckan.ini`.
- NGINX: `resolver` Docker dinamico per l'upstream (niente 502 dopo un rebuild di ckan) e timeout 600s.

## `2026-09-12` — Fase 3: ckanext-dcat 2.4.4 (DCAT-AP 3) + ckanext-dcatita
- `ckanext-dcat` upstream **v2.4.4** (DCAT-AP 3, CKAN 2.12, Python 3.14) al posto della copia patchata basata su un master 2024. Profilo di default `euro_dcat_ap_3` (funziona senza ckanext-scheming: il ramo scheming si autodisattiva).
- Le ~1.400 righe di patch storiche sono state riscritte come estensione **`ckan/ckanext-dcatita`** che usa le interfacce ufficiali (`IDCATRDFHarvester`, `IDCATURIGenerator`, `ckan.rdf.profiles`): plugin `dcatita_harvest`, `dcatita_uri`, profilo `dcat_ita`. Le mappe per ente (URI dei subcatalog, publisher, licenze, formati, media type) stanno in `subcatalogs.json`.
- Restano 4 patch minime in `ckan/patches/ckanext-dcat-patches/` (subcatalog dell'organizzazione via `site`, `dcat:service`, `dcatapit:Catalog`/`dct:issued`/`themeTaxonomy`, `fq` multipli ed esclusione RESTRICTED per l'harvest EDP, file-type nel JSON harvester).
- Differenze volute: `access_rights` non viene piu' forzato a PUBLIC se la sorgente dichiara RESTRICTED (DGA); gli errori di validazione in creazione non vengono piu' nascosti.

## `2026-09-12` — Fase 2: ckanext-harvest 1.6.3
- `ckanext-harvest` upstream **v1.6.3** (supporto ufficiale CKAN 2.12) installato in editable + 2 patch locali in `ckan/patches/ckanext-harvest-patches/` (normalizzazione cataloghi federati in `ckanharvester.py`; harvest source con URL duplicato non bloccante). La copia vendorizzata e' stata rimossa: gli upgrade futuri sono `@vX.Y.Z` nel Dockerfile + riapplicazione patch.
- Consumer `gather` e `fetch` come servizi Compose (`ckan-gather`, `ckan-fetch`) al posto di supervisord.

## `2026-09-12` — Fase 1: CKAN 2.12.0 su Python 3.14
- Nuova repo `ckan-docker-ita-212`: base `ckan/ckan-base:2.12.0-py3.14`, solo core + `ckanext-xloader` 2.5.0 (editable sotto `/srv/app/src`, altrimenti il namespace `ckanext` non lo vede).
- Solr `ckan/ckan-solr:2.12-solr9` con `managed-schema` = schema ufficiale 2.12.0 + campi custom dcatapit/multilang (`dcat_theme`, `dcat_subtheme`, `resource_license`, dynamicField `dcat_subtheme_*`, `organization_region_*`, `resource_license_*`, `package_multilang_localized_*`).
- `SECRET_KEY` al posto di `beaker.session.secret`; `recline_view` rimosso (non esiste da 2.11); worker `ckan jobs worker` come servizio Compose; `EXTRA_UWSGI_OPTS` gestito nativamente dall'immagine base (patch `04_patch_uwsgi.sh` rimossa).
- `.env.example` con `COMPOSE_PROJECT_NAME=ckan212`, nomi container `*212` e porte `8090/8453` per convivere con uno stack 2.10 sulla stessa macchina.
- Pylons/routes e `patches/base.py` non sono piu' installabili su Python 3.14: le estensioni che li usavano (dcatapit, oai-pmh, edp-mqa) verranno riportate su `ckan.plugins.toolkit` nelle fasi 3-5.

---
## Storico della repo di origine (ckan-docker-ita, CKAN 2.10)


## `2026-06-01`
Pulizia e robustezza del setup Docker (versione demo):
- **Nessun dominio hardcoded**: `ckan.oaipmh.base_url` e `ckanext.dcat.base_uri` sono derivati da `CKAN_SITE_URL`; aggiunta variabile opzionale `CKAN_OAIPMH_BASE_URL`. GeoNames parametrizzato via `GEONAMES_USERNAME`.
- **`.env.example` riscritto**: rimossi gli spazi attorno agli `=` (causa di valori con spazi spuri), blocco iniziale "DA MODIFICARE", `CKAN_VERSION=2.10.9`, `TZ=Europe/Rome`.
- **`docker-compose.yml`**: rimossa la chiave obsoleta `version`; eliminati gli override `environment:` sugli URL DB che divergevano dal `.env` sul `?sslmode=disable` (sorgente unica = `.env`); healthcheck CKAN con `start_period: 300s` per evitare lo stato `unhealthy` durante il caricamento dei vocabolari; healthcheck db/solr/redis con intervalli espliciti.
- **NGINX**: espone sia HTTP (`NGINX_PORT_HOST`) sia HTTPS (`NGINX_SSLPORT_HOST`); corretto l'ENTRYPOINT con `openssl` malformato (doppio `-keyout` verso directory inesistente); certificato self-signed generato una sola volta in `certs/`.
- **Setup gruppi**: lo script `03_ckan_groups.end` (estensione non eseguita dall'entrypoint) sostituito da `setup_groups.sh`, idempotente, copiato in `/srv/app/setup_groups.sh` ed eseguibile con `docker compose exec ckan bash /srv/app/setup_groups.sh`.
- **Dockerfile CKAN**: `apt-get update && apt-get install -y nano curl` (prima `apt install nano` falliva); corretto `chmod` che puntava al file sbagliato (`topics.json` -> `regions.rdf`).
- **Repo ripulito**: rimossi `__pycache__/`, `*.pyc`, file `*.orig`/`*.old`/`*.pyintermedio` e la chiave TLS privata committata in `nginx/setup/`.


## `2026-03-15`
E' stato inserito il file bash [04_patch_uwsgi.sh](https://github.com/piersoft/ckan-docker/blob/master/ckan/docker-entrypoint.d/04_patch_uwsgi.sh) che estende lo star_ckan.sh con  gli EXTRAS di uSWGI. Nel file .env è stato inserito EXTRA_UWSGI_OPTS=--http-timeout 600 --socket-timeout 600 --ignore-sigpipe --ignore-write-errors --disable-write-exception che estende il time out del CKAN nella creazione dei catalog.rdf/ttl, da 60 secondi a 600 per i cataloghi molto grossi o CKAN sottodimensionati

## `2026-02-19`
Estensione patchata per OAI-PMH per l'interfacciamento con OPENAIRE. Configurare lo script /docker-entrypoint.d/01_setup_xloader.sh con l'url del proprio server al posto di piersoftckan.biz. Esempio https://www.piersoftckan.biz/oai?verb=ListMetadataFormats oppure https://www.piersoftckan.biz/oai?verb=Identify o. Per elenco totale da una data --> https://www.piersoftckan.biz/oai?verb=ListRecords&metadataPrefix=oai_datacite&from=2026-01-01.
## SE NON  SERVE OpenAIRE cancellare dcat_ap_edp_mqa in 01_setup_xloader.sh in ckanext.dcat.rdf.profiles e nel file .env nella sezione plugin

## `2026-02-13`
Migrazione al CKAN 2.10.9 e fix vari

## `2026-02-10`
Fix docker-compose.yml per errore primo avvio

## `2026-01-27`
Inserito file css.example con il css da inserire nel Front End dell'Admin, nel caso si voglia avere un layout diverso.

## `2026-01-07`
Patch per hasPart come subcatalog per le organizzazioni create in locale
dovete sempre e solo accertarvi che quando create una organizzazione il campo URL sia sempre valorizzato (diventa il site e quindi la URI del subcatalog).

## `2025-12-24`
Eliminato il Datapusher ed inserito di Xloader

## `2025-12-22`
Patch del 2025-04-09 disattivata e abilitato il recepimento automatico della url tramite ckan_site_url

## `2025-12-20`
Risolto bug per HVD non valorizzati nelle modifiche manuali e che generavano extras hvd_category: "" al posto di non creare proprio la proprietà

## `2025-09-15`
test per Postgres16 nativamente supportato. Modificati i files Docker e .yml. Beta

**DATA.EUROPA.EU** richiede che le accessURL e i downloadURL siano raggiunbili in HEAD con risposta 200. Testare le proprie risorse con CURL -I URL 

Versione beta, stabile

~~## `2025-04-09`~~
OBSOLETA: ~~nel file [__euro_dcat_ap.py__](https://github.com/piersoft/ckan-docker/blob/master/ckan/patches/ckanext-dcat/ckanext/dcat/profiles/euro_dcat_ap.py) è inserita una patch delicata. l'accessURL viene sostituito con la landingpage della risorsa sul CKAN e il downloadURL viene popolato con il valore di download della risorsa (ex accessURL). Sostituire il path del dominio con il proprio portale CKAN:~~

	    if dataset_dict.get('id'):
               resource_dict['access_url']='https://www.piersoftckan.biz/dataset/'+dataset_dict['id']+'/resource/'+resource_dict['id']

~~Se NON si vuole tale trasformazione, commentare le due righe di codice precedenti. il downloadURL, in tal caso, verrà impostato identico all'accessURL~~

## `2024-09-27`
Il codice è al 99,999% pronto per una installazione stand alone. le patch che ogni tanto aggiorno sono per harvesting di cataloghi remoti. Se non è il vostro caso, credo che si possa considerare stabile.

## `2024-06-27`
La mappatura automatica dei GRUPPI durante gli harvesting, è settata manualmente nel file [mapping.py](https://github.com/piersoft/ckan-docker/blob/master/ckan/patches/ckanext-dcatapit/ckanext/dcatapit/mapping.py) (estensione DCATAPIT) e non in nella variabile ckanext.dcatapit.theme_group_mapping.file in ckan.ini. Punta a /srv/app/patches/theme_to_group.ini . Questo file viene copiato automaticamente in quella posizione, non bisogna fare nulla nella compilazione da Docker proposta. Se si fanno configurazioni differenti, va modificato il path.

## `2024-06-20`
RISOLTO HARVESTING SIA IN RDF/TTL CHE CON DCAT JSON. ESEGUIRE 2 VOLTE L'HARVESTING PER ATTIVARE PATCH SUCCESSIVE SU FORMATI,ACCESS_RIGHTS ect

## `2024-06-19`
SE SI VUOLE AVERE IL FILTRO HVD CATEGORY modificare in ckan.ini -> search.facets = organization groups tags res_format license_id hvd_category

## `2024-06-18`
PRESENTI ANCORA ALCUNI BUG IN HARVESTING JSON. 

## `2024-06-07`
AGGIORNATO FRONTEND DI CKAN CON HVD, ACCESS SERVICE E APPLICABLE LEGISLATION. 

## `2024-06-01`
VERSIONE NON STABILE E CON MOLTI ERRORI: DA NON USARE IN PRODUZIONE. 















