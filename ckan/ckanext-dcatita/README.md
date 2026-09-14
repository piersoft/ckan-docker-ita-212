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

## Note su casi reali gestiti

- `access_url_from_download` (INPS, Comune di Palermo): `dcat:accessURL` = `downloadURL`.
  Il fallback e' a cascata (`download_url` → `url` → pagina risorsa CKAN): su dati.gov.it
  alcune risorse INPS senza `download_url` generavano un accessURL vuoto e facevano
  fallire `catalog.ttl`.
- Tutti i match per ente passano da `rules.match_subcatalog()`, che normalizza i campi
  mancanti a stringa vuota: nessun `TypeError` su `holder_identifier` assente.
