# ckanext-dcatita

Regole "italiane" (dati.gov.it / DCAT-AP_IT) sopra **ckanext-dcat 2.x**, senza fork.
Sostituisce le ~1.400 righe di patch che ckan-docker-ita (CKAN 2.10) applicava
a `processors.py`, `harvesters/rdf.py`, `profiles/euro_dcat_ap*.py`.

## Plugin

| plugin | interfaccia | cosa fa |
|---|---|---|
| `dcatita_harvest` | `IDCATRDFHarvester` | normalizza i dataset harvestati prima di `package_create/update`: `notes`/`tags` `N_A`, `frequency` `UNKNOWN`, identificatori sanitizzati, email sporche, landing page, `access_rights` PUBLIC se assente, `hvd_category`/`applicable_legislation` scalari, date `temporal*` a `YYYY-MM-DD`, dedup extras, formati e licenze delle risorse, extras `source_catalog_*` dal file dei subcatalog; TLS non verificato verso i cataloghi PA (`ckanext.dcatita.harvest_verify_ssl`) |
| `dcatita_uri` | `IDCATURIGenerator` | URI `dcat:Dataset` con la base del catalogo d'origine (`base_uri` in `subcatalogs.json`) |
| profilo `dcat_ita` | `ckan.rdf.profiles` | rifinisce il grafo prodotto dagli altri profili: `dct:accessRights`/`dct:rights` come `RightsStatement`, frequenza/tema/lingua a URI EU, `accessURL` = pagina risorsa CKAN, `downloadURL`, licenze canoniche, formato + `dcat:mediaType` IANA, `byteSize` default, checksum, `dct:type`/`dct:identifier` del publisher dal codice IPA, URI `dcat:Distribution` del catalogo d'origine |

## Configurazione

```ini
ckan.plugins = ... dcat dcat_rdf_harvester ... dcatita_harvest dcatita_uri
ckanext.dcat.rdf.profiles = euro_dcat_ap_3 it_dcat_ap dcat_ita   ; dcat_ita SEMPRE per ultimo
ckanext.dcat.expose_subcatalogs = True

; facoltative
ckanext.dcatita.subcatalogs_file = /srv/app/patches/subcatalogs.json
ckanext.dcatita.harvest_verify_ssl = false
ckanext.dcatita.default_applicable_legislation = true
```

## `subcatalogs.json`

Un record per catalogo federato, match per sottostringa su `holder_identifier`
(codice IPA) o altro campo (`match_field`). Vedi il campo `_doc` nel file.
Aggiungere un ente = aggiungere una riga, non codice.

## Differenze volute rispetto alle patch 2.10

- `access_rights` viene impostato a PUBLIC **solo se assente**: un `RESTRICTED`
  dichiarato dalla sorgente (DGA) non viene piu' sovrascritto.
- gli errori di validazione in creazione restano errori dell'harvest object
  (non vengono piu' nascosti con `return True`).

## `dcat:landingPage` (usato da dcatapit)

`rules.landing_page()` calcola la landing page dei dataset in base alla chiave
`landing` della voce in `subcatalogs.json` (`mode`: `name`, `uri`, `url`, `fixed`;
`base`; `slash`; `strip`). Il profilo `it_dcat_ap` di ckanext-dcatapit la chiama al
posto delle ~200 righe di `if holder_identifier` che aveva nel 2.10: dcatapit dipende
quindi da ckanext-dcatita a runtime.

## `dct:provenance` (indicatore MQA "Origine")

`dcatita_harvest` compila `provenance` sui dataset harvestati che non ce l'hanno,
usando solo dati gia' presenti: ente titolare, catalogo d'origine, URL della harvest
source. Se non bastano, il campo resta vuoto (nessun testo generico).

Sugli stack dove non si vuole attivare l'intero `dcatita_harvest` (es. CKAN 2.10, dove
le normalizzazioni sono ancora patch dentro ckanext-dcat) c'e' il plugin autonomo
**`dcatita_provenance`**, che fa solo questo.

Testo predefinito:
> Dataset pubblicato da {holder_name} nel catalogo {source_catalog_title}
> ({source_catalog_homepage}), acquisito da {site_title} tramite harvesting.

Personalizzabile con `ckanext.dcatita.provenance_template`.

## Compatibilita' con CKAN 2.10 / ckanext-dcat 1.x

L'import di `IDCATURIGenerator` (introdotta in ckanext-dcat 2.4) e' condizionale, quindi
l'estensione resta importabile anche con dcat 1.x (senza il plugin `dcatita_uri`).

Nota: sullo stack 2.10 (`piersoft/ckan-docker-ita`) le estensioni sono **vendorizzate in
`patches/`** e copiate nell'immagine, non installate da qui: li' la stessa regola di
`dct:provenance` vive in-place a fine `parse_dataset` del profilo `it_dcat_ap`
(`patches/ckanext-dcatapit/.../dcat/profiles.py`, patch 28.09.26), con
`ckanext.dcatapit.provenance_template` come chiave di configurazione. Le due
implementazioni vanno tenute allineate a mano.

## Note su casi reali gestiti

- `adms:status` = `.../distribution-status/COMPLETED` su ogni distribuzione con un URL
  reale: lo chiede il modello MQA 0-7,5 di data.europa.eu. Non sovrascrive uno status
  dichiarato dalla sorgente (Deprecated, Withdrawn...). `accessURL` non e' un criterio
  utile per decidere se la risorsa esiste, perche' e' sempre valorizzato con la pagina
  risorsa CKAN.

- `access_url_from_download` (INPS, Comune di Palermo): `dcat:accessURL` = `downloadURL`.
  Il fallback e' a cascata (`download_url` → `url` → pagina risorsa CKAN): su dati.gov.it
  alcune risorse INPS senza `download_url` generavano un accessURL vuoto e facevano
  fallire `catalog.ttl`.
- Tutti i match per ente passano da `rules.match_subcatalog()`, che normalizza i campi
  mancanti a stringa vuota: nessun `TypeError` su `holder_identifier` assente.

## Etichetta DGA

I dataset con `dct:accessRights` = `.../access-right/RESTRICTED` (accesso limitato ai sensi
del Regolamento UE 2022/868, Data Governance Act) mostrano un'etichetta **DGA** accanto al
titolo, sia nei risultati di ricerca sia nella pagina del dataset. L'etichetta è un link
alla ricerca filtrata su quei soli dataset. Helper: `h.dcatita_is_restricted(pkg)`,
`h.dcatita_restricted_search_url()`; snippet riusabile: `snippets/dcatita_dga_badge.html`.

## Punteggio MQA nella scheda dataset (`edp_mqa`)

L'helper `h.dcatita_edp_mqa(pkg)` legge da data.europa.eu il punteggio MQA v2
(`datasetFinal`, scala 0-7,5) con cache Redis.

Lo stesso `dct:identifier` puo' arrivare a EDP da piu' cataloghi (p.es. un dataset
cartografico presente sia su dati.gov.it sia sull'RNDT): EDP assegna l'URI canonico a
chi arriva prima e il suffisso `~~N` agli altri, con metadati e punteggi diversi.
L'helper sceglie quindi la copia che appartiene al **proprio** catalogo, interrogando
`/datasets/<id>` per le varianti `~~1..~~3`; l'id del catalogo si imposta con
`ckanext.dcatita.edp_catalog` (default `dati-gov-it`).
