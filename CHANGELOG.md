# Changelog

## `2026-10-23` — Solr 9.10 e pulizia dei moduli non usati
- `solr/Dockerfile`: base `solr:9.10.1` ufficiale al posto di `ckan/ckan-solr:2.12-solr9` (fermo a Solr 9.9), con gli stessi passi dell'immagine CKAN. Corregge le vulnerabilita' di jetty, netty, jackson, zookeeper e solr-core segnalate da Trivy sulla 9.9. Indice compatibile: i volumi `solr_data` esistenti non vanno ricreati.
- Rimossi i moduli opzionali di Solr non usati da CKAN (`/opt/solr/modules`: Tika, OpenNLP, Kafka/cross-dc, Hadoop, repository cloud) e `prometheus-exporter`, con le loro librerie vulnerabili. Aggiunto `apt-get upgrade` (openssl).
- Immagine `ckan-db`: le segnalazioni restanti sono nel binario `gosu` dell'immagine ufficiale `postgres:16-alpine` (compilato con una versione di Go non aggiornata). Si usa solo all'avvio per passare all'utente postgres e il database sta su una rete interna; si chiudera' con l'aggiornamento dell'immagine ufficiale.

## `2026-10-23` — immagini Docker: aggiornamenti di sicurezza
- Immagine CKAN: `apt-get upgrade` in fase di build, per gli aggiornamenti di sicurezza Debian non ancora presenti in `ckan/ckan-base:2.12.0` (perl, libexpat1, libpcre2, libssh2: 3 vulnerabilita' critiche e varie alte segnalate da Docker Scout sulla 1.0.0).
- Librerie Python portate alle versioni corrette: `certifi>=2026.10.19`, `PyJWT>=2.14.0`, `urllib3>=2.8.0`, `msgpack>=1.2.1`, `setuptools>=78.1.1` (sotto la 81, che rimuove `pkg_resources` usato dai namespace `ckanext`).
- Restano segnalate da Trivy/Docker Scout solo le copie interne di pip (`pip/_vendor`: certifi, msgpack, urllib3, pkg_resources di setuptools): CKAN non le usa e si aggiornano solo con una nuova versione di pip (gia' l'ultima, 26.2.1).
- `scripts/build-push.sh`: con il push la build e' senza cache e con `--pull`, cosi' ogni versione pubblicata prende gli ultimi aggiornamenti; con `--no-push` resta la cache.

## `2026-10-23` — attribuzione del footer configurabile
- Il testo «rebuilt by …» del footer si imposta con `CKANEXT__DCATITA__FOOTER_REBUILT_BY`; vuoto (default) = `AgID`. Prima era fisso «rebuilt by Piersoft».

## `2026-10-23` — CSS accessibile predefinito
- Il tema accessibile (WCAG 2.1 AA) è ora predefinito: `css.example` si sposta in `ckan/css.example`, viene copiato nell'immagine e all'avvio lo script `docker-entrypoint.d/04_custom_css.sh` lo imposta come «Custom CSS» (chiave `ckan.site_custom_css`) se l'admin non ne ha uno proprio. Alle versioni successive viene aggiornato finché l'admin non lo modifica; un CSS modificato dall'admin non viene mai sovrascritto.
- Variabili `CKAN_CUSTOM_CSS_DEFAULT` (default `true`; `false` disattiva) e `CKAN_CUSTOM_CSS_FORCE` (`true` sovrascrive col predefinito al prossimo avvio).
- Il logo CKAN del footer usa un URL assoluto (`/base/images/ckan_logo_col.png`): con quello relativo, nel CSS inserito nella pagina, l'immagine non si caricava nelle pagine annidate (es. pagina risorsa).

## `2026-10-23` — accessibilita' WCAG 2.1 AA del front end
- **Traduzioni**: `ckanext-dcatita` porta un catalogo italiano con le stringhe del core rimaste vuote (skip link «Salta al contenuto principale», ricerca, «Apri o chiudi il menu di navigazione», etichette `aria-label` di dataset, risorse e filtri) e corregge «Linguaggio» in «Lingua» e «Data e Risorse» in «Dati e risorse».
- **Homepage**: `h1` con il titolo del sito quando c'e' il testo introduttivo; titoli di gruppi e organizzazioni in evidenza h2 e dataset h3 (prima h3 con dentro h2); immagini decorative fuori dal tab; tolta la «sezione in evidenza» d'esempio con immagine segnaposto e link a `#`.
- **Paginazione** (patch 04 al core): `<nav>` con etichetta, frecce con testo per i lettori di schermo, `aria-current` sulla pagina corrente, puntini non piu' link.
- **Filtri di ricerca**: l'etichetta dice nome completo e numero di dataset (prima nome troncato e nome tecnico del campo); filtro attivo annunciato come tale.
- **Risorse**: «Esplora» e' un `<button>` con id univoco (prima `dropdownExplorer` ripetuto); l'etichetta del link dice nome e formato della risorsa.
- **Footer**: link «Dichiarazione di accessibilita'» se e' impostato `CKANEXT__DCATITA__ACCESSIBILITY_STATEMENT_URL`.
- **`css.example`**: revisione completa (focus visibile nell'header, contrasto del menu, link del footer sottolineati, campi dei form piu' grandi, pulizia delle regole duplicate); tolto il titolo d'esempio dell'ente aggiunto via CSS.

## `2026-10-22` — immagini pronte su Docker Hub
- Quattro immagini da pubblicare su Docker Hub: `piersoft/ckan` (anche per i worker), `piersoft/ckan-solr` (schema DCAT-AP_IT incluso), `piersoft/ckan-db` (creazione database CKAN e DataStore), `piersoft/ckan-nginx`. Tag `2.12-dcatapit-X.Y.Z`, `2.12` e `latest`.
- Nuovo `docker-compose.hub.yml`: avvio senza build e senza clonare il repository, solo con il compose e il `.env` (`.env.hub.example`, con porte 8080/8443 e nomi senza suffisso). Versione delle immagini in `CKAN_ITA_TAG`.
- Nuovo `scripts/build-push.sh <versione>`: build (linux/amd64) e push delle quattro immagini con le label OCI. Da lanciare dopo `docker login`.
- Nuovo `README-dockerhub.md`: descrizione per la pagina Docker Hub.
- Immagine CKAN: nuovo entrypoint `ckan/setup/ckan-ita-entrypoint.sh`. Se nel `.env` i segreti (`SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, JWT) mancano o sono `CHANGE_ME`, li genera una volta e li conserva nel volume `ckan_storage`, condiviso con i worker. Con segreti reali nel `.env` non cambia nulla.
- Nuovo `ckan/docker-entrypoint.d/03_setup_groups.sh`: con `CKAN_SETUP_GROUPS=true` i gruppi tematici vengono creati da soli al primo avvio (in background, appena il web server risponde; marker nel volume). Default spento: resta valido il comando manuale `setup_groups.sh`.
- OAI-PMH: `Identify` su un catalogo vuoto (installazione nuova) dava errore 500, perche' la data del primo dataset non esisteva. Ora usa la data corrente finche' non ci sono dataset.
- OAI-PMH: l'email nella risposta Identify non e' piu' fissa nel codice; viene da `CKAN_OAIPMH_ADMIN_EMAIL` o, se vuota, da `CKAN_SYSADMIN_EMAIL`. **Istanze esistenti**: per mantenere l'indirizzo attuale impostare `CKAN_OAIPMH_ADMIN_EMAIL` nel `.env`.

## `2026-10-22` — validatore: «raccomandata» e «obbligatoria» secondo la gravita'; parole chiave tra le indicazioni AgID
- Le regole piveau usano lo stesso vincolo (`sh:minCount`) per le proprieta' obbligatorie (Violation) e per quelle raccomandate (Warning, profilo «EDP · raccomandate»). Il messaggio tradotto diceva sempre «Proprieta' obbligatoria assente»; ora dice «Proprieta' raccomandata assente» quando la gravita' e' Warning. Vale per il validatore web e il report settimanale.
- Nuova indicazione AgID (Info): dataset senza parole chiave (`dcat:keyword`), richieste per l'harvesting su dati.gov.it e valutate dall'MQA.

## `2026-10-21` — indicazione AgID: prefisso dell'editore invece che del titolare
- Quando il prefisso dell'identificativo del dataset non e' il codice IPA del titolare ma quello dell'editore (`dct:publisher`), l'indicazione ha un messaggio proprio: «il prefisso e' il codice IPA dell'editore, non quello del titolare: l'identificativo va costruito con il codice IPA del titolare», con i due codici nel valore. Caso tipico: un comune che pubblica nel proprio catalogo dataset di cui e' titolare una societa' partecipata. Resta un'indicazione (Info) e la regola resta sul titolare.

## `2026-10-21` — validatore: dataset con piu' titolari (DCAT 3)
- DCAT-AP_IT: `dct:rightsHolder` del dataset ora e' 1..N, come previsto con DCAT 3 (dataset aggregati con piu' enti titolari). Prima la regola ne ammetteva uno solo e segnalava una violazione per ogni dataset con piu' titolari.
- Indicazione AgID sul prefisso dell'identificativo: con piu' titolari basta che il prefisso coincida con il codice IPA di uno di loro (prima si guardava solo il primo letto).

## `2026-10-21` — dcatapit: il vocabolario licenze non viene piu' alterato dall'harvest
- Nella lettura della licenza (parse della distribuzione) il codice modificava `document_uri` e `uri` della riga del vocabolario licenze restituita da `get_license_from_dcat()`. Quella riga e' un oggetto SQLAlchemy della sessione: al commit dell'harvest la modifica restava nel database e valeva da quel momento per tutti i dataset con quella licenza. Esempi visti: su dati.puglia.it CC BY-SA esce come `http://creativecommons.org/licenses/by/4.0/` (con tipo e nomi BY-SA); su dati.gov.it lo stesso indirizzo descrive insieme CC BY e IODL 1.0. Il ramo DGA poteva trasformare in OtherRestrictiveClauses la licenza di tutti i dataset.
- Ora le sostituzioni si fanno su variabili locali (`lic_uri`, `doc_uri`); il risultato per il singolo dataset non cambia.
- **Da fare una volta su ogni istanza gia' in esercizio**, per ripulire il vocabolario: `ckan dcatapit load --filename <ckanext-dcatapit>/vocabularies/licences.rdf` (svuota e ricarica le licenze; le risorse conservano la loro licenza, salvata come URI). Il catalogo esposto si corregge subito, senza nuovo harvest.

## `2026-10-20` — IRI relativi mostrati come scritti nel catalogo
- Un IRI relativo nel catalogo (es. `vcard:hasEmail <opendatamilano@comune.milano.it>`, senza `mailto:`) veniva completato con la cartella di chi esegue lo script: nel report compariva `file:///home/.../opendatamilano@comune.milano.it`, un percorso del server che non c'entra con l'ente. Ora i dati si leggono con una base fittizia (`https://iri-relativo.invalid/`) e il valore si mostra com'e' scritto, con la nota "(IRI relativo: manca lo schema, es. mailto: o https://)".
- Vale per il validatore web, `validate_edp_shacl.py` e il report settimanale.

## `2026-10-20` — indicazioni AgID: temi e formati segnaposto
- Script di validazione: nuove indicazioni (Info) per tema e formato `OP_DATPRO` («dati provvisori», segnaposto) e per il formato `ARC` (quasi sempre scelto per errore).

## `2026-10-20` — validatore: punto ammesso nell'identificativo del dataset
- L'indicazione AgID sull'identificativo `codiceIPA:identificativo` ora accetta anche il punto dopo i due punti (es. `c_e506:scuole.2026`): CKAN e dcatapit non limitano i caratteri dell'identificativo (lo richiedono solo non vuoto e unico). Restano esclusi spazi, accenti, barre e altri caratteri; il codice IPA prima dei due punti resta lettere, cifre e `_`.

## `2026-10-20` — script di validazione: codice IPA con maiuscole e minuscole
- Nel profilo `agid` il codice IPA del titolare deve essere scritto come in IndicePA (`UNITO`, non `unito`), e il prefisso dell'identificativo deve coincidere esattamente. Allineato allo stack 2.10.

## `2026-10-20` — script di validazione: codice IPA del titolare su IndicePA
- Nel profilo `agid` di `tools/validate_edp_shacl.py` il codice IPA del titolare viene cercato nel dataset "enti" di IndicePA; se e' il codice di un'unita' organizzativa o un codice fiscale, l'indicazione riporta il codice IPA da usare. `--no-ipa` salta la verifica. Allineato allo stack 2.10.

## `2026-10-20` — script di validazione: formati e media type sugli elenchi di data.europa.eu
- `tools/validate_edp_shacl.py --profile vocabolari` controlla `dct:format` sul vocabolario EU `file-type` e `dcat:mediaType` sul registro IANA, con gli elenchi di data.europa.eu in `tools/shapes/vocabolari-elenchi.ttl`. Il file si rigenera a mano con il nuovo `tools/aggiorna_vocabolari.py`. Allineato allo stack 2.10.

## `2026-10-19` — script di validazione: regole AgID come indicazioni
- Nel profilo `agid` di `tools/validate_edp_shacl.py` tutte le segnalazioni sono ora `Info`: sono indicazioni operative AgID, non regole DCAT, e non cambiano l'esito ne' il codice di uscita. Allineato allo stack 2.10.

## `2026-10-19` — script di validazione: regole operative AgID
- `tools/validate_edp_shacl.py` e `tools/shapes/agid.ttl` allineati allo stack 2.10: nuovo profilo `agid` (identificativo `codiceIPA:identificativo` con prefisso uguale al codice IPA del titolare, email dell'editore del catalogo non PEC) e percorsi a sequenza mostrati per intero. Dettagli nel CHANGELOG di ckan-docker-ita.

## `2026-10-17` — `dct:relation`: ricerca per titolare invece dell'organizzazione
- Il ripiego di `dct:relation` (metrica MQA `relationAvailability`) puntava a `<site_url>/organization/<org>`. Su un portale federato come dati.gov.it le organizzazioni sono i cataloghi, non i titolari: il dataset di ASSET Puglia sta sotto `regione-puglia`.
- Inoltre lo stack 2.10 scriveva `https://www.dati.gov.it/view-dataset?organization=<org>` con l'organizzazione del portale di origine (es. `asset-puglia` da dati.puglia.it), che su dati.gov.it non esiste: il valore arrivava con l'harvest nell'extra `related_resource` e veniva ri-esposto.
- Correzione in `ckanext-dcatita` (`profile.py`, `rules.holder_relation_url`):
  - i valori `...view-dataset?organization=...` vengono scartati in serializzazione, anche se arrivano dall'harvest;
  - il ripiego punta alla ricerca dei dataset dello stesso titolare (`holder_name`; se manca, il titolo dell'organizzazione). Formato con `CKANEXT__DCATITA__RELATION_URL`; vuoto = `{site_url}/dataset/?holder_name=<titolare>`; per dati.gov.it `https://www.dati.gov.it/view-dataset?holder_name={qholder}`.
  - il titolare si legge prima dagli extra: nei risultati di `package_search`, che alimentano `catalog.ttl`, `holder_name` di primo livello vale il titolo dell'organizzazione (verificato su `synthetic-photovoltaic-data`: primo livello "Master class", titolare vero "Università del Salento").

## `2026-10-17` — publisher dei sottocataloghi con valori vuoti
- Il `dct:publisher` dei sottocataloghi usciva con `foaf:mbox ""` e, quando mancavano, con `foaf:homepage <>` e `dct:type <>`: i campi `email`, `url` e `type` vuoti dell'extra `source_catalog_publisher` (o del publisher di ripiego) venivano scritti lo stesso. Il ciclo saltava solo i valori assenti, non le stringhe vuote.
- Correzione nella nuova `patches/ckanext-dcat-patches/08_publisher_empty.patch` (su `processors.py` di ckanext-dcat v2.4.4, ciclo `publisher_sources`): anche i valori vuoti vengono saltati. `foaf:name` non cambia, perche' viene ricavato prima se manca.

## `2026-10-16` — landing page dei dataset delle Camere di Commercio verso mistralportal.it
- I dataset con `cci` nell'identificativo del titolare (Camere di Commercio) uscivano con `dcat:landingPage` su `https://www.mistralportal.it/...`. Il portale MISTRAL non esiste piu': il dominio rimanda alla home di MeteoHub (Agenzia ItaliaMeteo), quindi quelle landing page non portano al dataset. Su dati.gov.it erano circa 500 dataset, tra cui quelli della Camera di Commercio di Lecce pubblicati su dati.puglia.it.
- Correzione: tolta la regola in `ckanext-dcatita/.../subcatalogs.json`. Questi dataset ora hanno la landing page del portale che li pubblica, come gli altri.
- I dataset harvestati si correggono al successivo harvest del portale di origine.

## `2026-10-16` — lingua dei sottocataloghi harvestati scelta a caso tra quelle della sorgente
- I cataloghi sorgente possono dichiarare piu' lingue: per esempio Crispiano e Copertino dichiarano DEU, ENG, FRA, ITA e il letterale `"it"`. In fase di harvest l'extra `source_catalog_language` ne prendeva una qualsiasi (`_object_value`), quindi i sottocataloghi uscivano con `DEU`, `FRA` o `ENG` invece di `ITA`, e il valore poteva cambiare da un harvest all'altro.
- Correzione nella nuova `patches/ckanext-dcat-patches/07_catalog_language.patch` (su `profiles/base.py` di ckanext-dcat v2.4.4, `_extract_catalog_dict`): si sceglie l'italiano; altrimenti la prima lingua in ordine alfabetico. Una lingua impostata in `subcatalogs.json` continua ad avere la precedenza.
- Verificato che le sette patch si applichino in sequenza su ckanext-dcat v2.4.4. L'extra viene scritto al momento dell'harvest: i sottocataloghi gia' importati si correggono al successivo harvest.

## `2026-10-16` — `dcatap:availability` con `https://`
- `dcatap:availability` usciva con `https://publications.europa.eu/resource/authority/planned-availability/...`: le authority table EU usano `http://`, quindi il valore non corrispondeva ad alcun concetto del vocabolario. Lo generavano le opzioni del modulo in `ckanext-dcatapit/.../schema.py`, e arriva uguale anche da alcuni cataloghi harvestati.
- Correzione: il profilo `dcat_ita`, ultimo della catena, riporta a `http://` i valori di `dcatap:availability` delle distribuzioni, compresi quelli gia' salvati e quelli harvestati; nel modulo di `ckanext-dcatapit` le due opzioni ora hanno il valore `http://`.
- `tools/shapes/vocabolari.ttl`: media type IANA accettati con `http`/`https` e con o senza `www`, come fa EDP.

## `2026-10-16` — `spdx:checksum` doppio sulle distribuzioni
- Con il profilo `dcat_ap_edp_mqa` attivo ogni distribuzione con un hash usciva con due nodi `spdx:checksum` identici: una Violation EDP (`sh:maxCount 1`) per distribuzione.
- Causa: `MqaEuropeanDCATAP2Profile` eredita da `euro_dcat_ap_3` e richiama `super().graph_from_dataset()`, quindi il codice europeo delle distribuzioni gira due volte. Il checksum e' un nodo anonimo creato con un `BNode()` nuovo, quindi restava doppio; le triple con URI invece si fondono da sole.
- Correzione nella nuova `patches/ckanext-dcat-patches/06_checksum.patch` (su `profiles/euro_dcat_ap_base.py` di ckanext-dcat v2.4.4): il checksum non viene aggiunto se la distribuzione ne ha gia' uno con lo stesso valore. Senza `hash_algorithm` l'algoritmo si ricava dalla lunghezza dell'hash (32 MD5, 40 SHA-1, 64 SHA-256); prima mancava del tutto.
- Verificato che le sei patch si applichino in sequenza su ckanext-dcat v2.4.4. Stessa correzione dello stack CKAN 2.10.

## `2026-10-16` — lingua dei sottocataloghi emessa come testo
- Nei sottocataloghi `dct:language` usciva come stringa (`"http://publications.europa.eu/resource/authority/language/ITA"`): Violation EDP `sh:BlankNodeOrIRI`, una per sottocatalogo. Il `processors.py` upstream di ckanext-dcat v2.4.4 aggiunge l'extra `source_catalog_language` sempre come `Literal`.
- Correzione in `patches/ckanext-dcat-patches/01_processors.patch`: nuova funzione `_catalog_language`. Un URI resta URI (`https://publications.europa.eu/` riportato a `http://`), un codice a 3 lettere diventa `.../language/ITA`, uno a 2 lettere (`it`, `en`, `de`, `fr`, `es`) viene convertito; ogni altro valore resta letterale.
- Verificato che le cinque patch si applichino ancora in sequenza su ckanext-dcat v2.4.4. Stessa correzione dello stack CKAN 2.10.

## `2026-10-16` — `tools/validate_edp_shacl.py`: profili italiani
- Allineato alla versione dello stack CKAN 2.10. Nuova opzione `--profile`: oltre al profilo EDP (default, invariato) valida con `dcatapit` (Linee guida AgID per i cataloghi dati), `vocabolari` (authority table EU) e `hvd` (dati di elevato valore, Reg. UE 2023/138); `it` li attiva tutti e tre, `tutti` aggiunge anche EDP.
- Le shape italiane stanno in `tools/shapes/`. `--file` accetta anche RDF/XML e JSON-LD.

## `2026-10-13` — licenze harvestate trasformate in CC BY 4.0
- Su ogni dataset harvestato la licenza finiva in CC BY 4.0 anche quando il catalogo sorgente dichiarava altro (es. IODL 2.0 con `A29_IODL20`). Unica eccezione: le licenze CC0, salvate dal controllo `publicdomain`.
- Causa, in `ckanext-dcatapit/.../dcat/profiles.py`: le `license.replace(...)` trasformano il nodo `URIRef` della licenza in una `str` semplice. Le letture successive dal grafo (`dct:type`, `foaf:name`, `versionInfo`) usavano quella `str`, e rdflib non la riconosce come URI: zero risultati. Con `names` vuoto si entrava nel ramo di ripiego, che imposta `license_name` = CC BY 4.0, `license_type` = `A21_CCBY40` e `document_uri` = creativecommons by/4.0. Per lo stesso motivo la toppa per `r_lazio` veniva sovrascritta subito dopo.
- Correzione: il nodo originale viene salvato in `license_node` prima delle sostituzioni, e le tre letture dal grafo usano `license_node`. Le sostituzioni restano invariate e continuano a valere per la ricerca nel vocabolario.
- Corretta anche `names.values()[0]` (sintassi Python 2, `TypeError` su Python 3) in `list(names.values())[0]`.
- Verificato sul `catalog.ttl` del Ministero della Salute: prima `A21_CCBY40` / "CC BY 4.0", dopo `A29_IODL20` / "Italian Open Data License 2.0 (IODL 2.0)".
- Stessa correzione del repo `ckan-docker-ita` (CKAN 2.10), commit `23ae1c4`.
- Effetto atteso al prossimo harvest: le sorgenti che dichiarano licenze diverse da CC BY 4.0 e CC0 (IODL, CC BY-SA, ODbL…) mostreranno la licenza reale invece di CC BY 4.0.

## `2026-10-11` — `foaf:page` tipizzato in ogni caso, non solo dove lo imposta il fallback
- La shape DCAT-AP 3.0 impone `sh:class foaf:Document` su `foaf:page` e il validatore non dereferenzia l'URI: il tipo va dichiarato nel grafo. Finora veniva dichiarato solo sul valore che il fallback imposta di sua iniziativa.
- Caso scoperto: l'extra `documentation` della risorsa, che alcuni cataloghi sorgente pubblicano e che il mapping generico di `euro_dcat_ap` riemette come `foaf:page` senza tipo. Il fallback lo salta per la guardia `if not any(g.objects(dist, FOAF.page))`, quindi quel `foaf:page` restava senza tipo.
- Ora vengono tipizzati tutti gli oggetti di `foaf:page` del dataset e delle sue distribuzioni, con un ciclo limitato al dataset corrente: in `catalog.ttl` il grafo contiene tutti i dataset della pagina, quindi una scansione globale per ogni dataset sarebbe quadratica.
- Il difetto del doppio `##` sulle landing page riguarda solo lo stack 2.10: qui la `dcat:landingPage` viene emessa cosi' com'e', senza appendere il separatore.
- Nessun effetto sul punteggio MQA: `documentationAvailability` verifica la sola presenza del predicato.

## `2026-10-10` — `dcat:landingPage` non sempre tipizzata `foaf:Document`
- `dcat:DatasetShape` di DCAT-AP 3.0 impone `sh:class foaf:Document` su `dcat:landingPage`, e il validatore non dereferenzia: il tipo va dichiarato nel grafo. Nel profilo `dcat_ita` non esisteva un blocco dedicato, quindi la landingPage veniva tipizzata solo **per effetto collaterale**, quando il fallback di `foaf:page` capitava di usarla.
- Conseguenza: sui dataset la cui sorgente fornisce gia' `foaf:page` il fallback non scatta, la landingPage resta un IRI nudo e la shape e' violata. Verificato su un dataset harvestato da Cruscotto Italia, che emette `foaf:page` di suo (`about.html#fonti`): la `dcat:landingPage` del dataset risultava non tipizzata.
- Aggiunto il blocco di tipizzazione subito dopo la pulizia delle landingPage. Sta nel profilo `dcat_ita`, che e' l'ultimo della catena, quindi copre anche le landingPage aggiunte da `it_dcat_ap`.

## `2026-10-09` — foaf:page puntava al dataset stesso (difetto introdotto in giornata)
- Verificato sul grafo in produzione: su dati.gov.it l'URI del dataset e' **esattamente** `https://www.dati.gov.it/view-dataset/dataset?id=<name>`, lo stesso URL che il fallback di `foaf:page` costruiva. Risultato: la distribuzione documentava il dataset stesso e il nodo del dataset si portava dietro un `rdf:type foaf:Document`.
- `foaf:page` ora usa, in ordine: `documentation`/`describedBy` della risorsa, altrimenti una `dcat:landingPage` gia' presente nel grafo. Piu' una guardia: il valore non puo' mai coincidere con `dataset_ref` ne' con la distribuzione.
- Conseguenza da accettare: i dataset senza landingPage e senza documentazione sulla risorsa non espongono `foaf:page`, quindi restano a 0 su `documentationAvailability`. Preferibile a un grafo sbagliato.
- Corretto anche un difetto preesistente: su dati.gov.it `dcat:landingPage` era un IRI nudo, mentre la shape `dcat:DatasetShape` impone `sh:class foaf:Document`. Ora il tipo e' dichiarato nel grafo, nel profilo `it_dcat_ap` che gira per ultimo, cosi' copre anche le landingPage aggiunte da dcatapit. Lo stack 2.12 le tipizzava gia'.

## `2026-10-09` — organization_list?all_fields=true: il campo era `identifier` (fix in dcatapit)
- Il campo che lasciava il sentinella `missing` in output e' **`identifier`**, confermato dalla risposta ora che l'endpoint torna 200: `[k for k,v in r.items() if v is None]` -> `['identifier']`.
- Meccanismo completo: `organization_list?all_fields=true` chiama `organization_show` per ogni organizzazione forzando `include_extras=False`; `convert_from_extras` non trova extras da convertire e la chiave resta a `missing`. Nella catena di `identifier` c'e' **solo** `not_empty`, che registra l'errore ma **non rimuove la chiave** (a differenza di `ignore_missing` e `ignore_empty`, che fanno `data.pop(key)`); `group_show` poi **scarta** gli errori (`group_dict, _errors = plugin_validate(...)`) e il sentinella finisce in `json.dumps`.
- Correzione: in `show_group_schema()` (2.12) / `db_to_form_schema()` (2.10) la catena diventa `[convert_from_extras, ignore_missing] + validator`. Messo qui e non in `get_custom_organization_schema()`, perche' quella lista serve anche a `create_group_schema`/`update_group_schema`: anteporre `ignore_missing` la' renderebbe `identifier` opzionale in scrittura.
- Nota: `hvd_category` NON era a rischio, come avevo ipotizzato in un primo momento: `ignore_empty` rimuove la chiave esattamente come `ignore_missing`. Solo le catene che iniziano con `not_empty` perdono il sentinella.
- La patch al core su `_json_serial` resta come rete di sicurezza per casi analoghi in altri schemi, non e' piu' la correzione.

## `2026-10-09` — organization_list?all_fields=true restituiva 500: _json_serial muto
- Nei log di produzione: `ERROR [ckan.config.middleware.flask_app] Unhandled Object` seguito da `500 /api/3/action/organization_list render time 0.295 seconds`. Il traceback finisce in `ckan/views/api.py` `_json_serial`, che per qualsiasi tipo diverso da `datetime`/`date` solleva `TypeError("Unhandled Object")` **senza dire quale oggetto**.
- Riscontri sul campo: `organization_list?all_fields=true` -> 500 su **entrambi** gli stack (2.10 su EKS e 2.12), `group_list?all_fields=true` -> 200, `organization_show` -> 200. Quindi il problema e' nelle sole organizzazioni e in una parte di codice comune ai due stack, non nell'immagine nuova.
- `limit` e `offset` non isolano il colpevole (provati 0, 1, 2, 5, 20, 100, 300: tutti 500): CKAN dictizza e ordina tutte le organizzazioni e applica il limite dopo, quindi basta un singolo valore non serializzabile per far cadere ogni chiamata. `organization_show` funziona perche' applica `db_to_form_schema()` di dcatapit, che passa gli extra per `convert_from_extras`; in modalita' `all_fields` nessuno schema viene applicato e il dict grezzo va diritto a `json.dumps`.
- Nuova patch al core `patches/ckan-core-patches/03_json_serial_diagnostica.patch`: `_json_serial` gestisce anche `time`, `timedelta`, `set`/`frozenset` e `bytes`, e per tutto il resto **logga tipo e repr** e degrada a stringa invece di far cadere la risposta. `Decimal` e `UUID` cadono di proposito nel ramo loggato, per vedere il campo responsabile.
- **Oggetto individuato**: `type=Missing` (`ckan.lib.navl.dictization_functions.Missing`), il sentinella che navl usa per le chiavi assenti. Non e' un dato sporco: e' una catena di validator che non rimuove la chiave.
- `Missing.__str__` **solleva** `Invalid('Missing value')`, quindi il fallback generico a stringa non bastava: il sentinella va intercettato prima. La patch ora lo mappa a `None`, come fa gia' CKAN in `MissingNullEncoder` ("json encoder that treats missing objects as null").
- Da dove arriva: in CKAN 2.12 `_group_or_org_list` con `all_fields=true` chiama `organization_show` per ogni organizzazione forzando `include_extras=False`. Gli schemi custom di dcatapit (`db_to_form_schema`) antepongono `convert_from_extras` a ogni campo: senza `extras` nel dict non c'e' nulla da convertire e la chiave resta a `missing`. Resta aperto quale campo: `identifier` ha `['not_empty']` e `hvd_category` ha `['ignore_empty']`, cioe' catene senza `ignore_missing` in testa. Si identifica dalla chiave a `null` nella risposta ora che l'endpoint torna 200.

## `2026-10-09` — le ultime 3 metriche MQA a zero: adms:identifier, dct:relation, foaf:page
- Rilevate sull'API MQA di data.europa.eu (`metricsVersion 2.0.0`): dataset **7,0/7,5**, distribuzioni **7,25/7,5**, `datasetFinal` **7,125**. Gli unici `result=0` erano `admsIdentifierAvailability`, `relationAvailability` (dataset) e `documentationAvailability` (distribuzione), 0,25 ciascuna.
- Il mapping in `euro_dcat_ap` esiste (extra `alternate_identifier`, `related_resource`, `documentation`): mancano i **valori**, perche' nessuno popola quegli extra. Aggiunti fallback deterministici in `profile.py`, coerenti con quanto fatto per `adms:status`, `dct:provenance` e `byteSize`.
- `adms:identifier`: nodo `adms:Identifier` con una sola `skos:notation` (id CKAN) — `dct:identifier` porta gia' quello DCAT-AP_IT.
- `dct:relation`: pagina dell'organizzazione sul portale (`<site_url>/organization/<name>`).
- `foaf:page` sulla distribuzione: `documentation`/`describedBy` della risorsa, altrimenti la pagina del dataset, **con `rdf:type foaf:Document` nel grafo** (la shape impone `sh:class foaf:Document` e il validatore non dereferenzia).
- Nessun valore passa da `URIRefOrLiteral`: le shape di `adms:identifier` e `dct:relation` impongono `sh:nodeKind sh:BlankNodeOrIRI`, un Literal genererebbe un warning nuovo.
- Sullo stack 2.10 lo stesso fix e' spezzato in due file: `adms:identifier` deve stare in `ckanext-dcatapit` perche' il profilo `it_dcat_ap` esegue `g.remove((dataset_ref, ADMS.identifier, None))` dopo `euro_dcat_ap`. Qui no: `dcat_ita` e' l'ultimo profilo della catena, quindi i tre blocchi stanno insieme.
- Atteso: dataset 7,5/7,5, distribuzioni 7,5/7,5, `datasetFinal` **7,5**.

## `2026-10-09` — adms:status: il warning SHACL di EDP non dipendeva dal vocabolario
- Il validatore di data.europa.eu (shape `dcatap300level1`, `:StatusRestriction`) segnalava `StatusRestrictionADMS` sulle distribuzioni. Verificato sull'endpoint SPARQL di EDP: il warning scatta con **entrambi** i vocabolari — 205.860 risultati con `purl.org/adms/status/Completed` e 17.216 con l'URI EU `distribution-status/COMPLETED` usato "nudo". Cambiare valore non bastava.
- La shape richiede `skos:inScheme <...distribution-status>` **sul grafo pubblicato**: il validatore non dereferenzia il NAL. Le uniche distribuzioni senza warning (circa 3.600 su EDP) usano l'URI EU **e** dichiarano il concetto nel grafo.
- Quindi: valore riportato al vocabolario EU (`DISTRIBUTION_STATUS_SCHEME + "/COMPLETED"`) e aggiunte le due triple `a skos:Concept` / `skos:inScheme` accanto a ogni `adms:status`.
- Nota: il punteggio MQA non era comunque intaccato — `statusAvailability` risulta 0,25 assegnato anche con l'URI ADMS, perche' quella metrica misura solo la presenza della proprieta'.

## `2026-10-03` — MQA: punteggio della copia giusta su data.europa.eu
- `edp_mqa` sceglieva fra le copie EDP dello stesso `dct:identifier` quella con `quality_meas.scoring` piu' alto: per i dataset presenti anche nell'RNDT finiva per mostrare il voto del record RNDT. Ora risolve la copia che appartiene al catalogo del portale (`ckanext.dcatita.edp_catalog`, default `dati-gov-it`), interrogando `/datasets/<id>` anche per le varianti `~~N` che la ricerca testuale non restituisce. Prefisso di cache portato a `v3`.
- Il controllo delle varianti fa piu' chiamate in sequenza: un singolo read timeout non fa piu' scattare il circuit breaker (si prova la variante successiva, l'errore si propaga solo se nessuna chiamata riesce) e il timeout di lettura passa da 5 a 8 secondi.
- Allineamento della stessa correzione fatta sullo stack 2.10 (`piersoft/ckan-docker-ita`, commit `d7ea2a1`).

## `2026-09-28` — dct:provenance sui dataset harvestati
- `dcatita_harvest` compila `provenance` quando manca, con i soli dati certi del dataset (ente titolare, catalogo d'origine, URL della harvest source); se non bastano, il campo resta vuoto. Copre l'indicatore MQA "Origine" (Riutilizzabilita', 0,25). Testo configurabile con `ckanext.dcatita.provenance_template`.
- Nuovo plugin autonomo `dcatita_provenance` (solo questa regola), per gli stack dove non si attiva l'intero `dcatita_harvest`.
- `ckanext-dcatita` reso importabile anche con ckanext-dcat 1.x (import condizionale di `IDCATURIGenerator`). Sullo stack 2.10, dove le estensioni sono vendorizzate in `patches/`, la stessa regola e' implementata in-place nel profilo `it_dcat_ap` di dcatapit: le due copie vanno tenute allineate.

## `2026-09-23` — adms:status sulle distribuzioni (modello MQA 0-7,5)
- Il profilo `dcat_ita` aggiunge `adms:status` = `.../distribution-status/COMPLETED` alle distribuzioni con un URL reale, senza sovrascrivere uno status gia' dichiarato dalla sorgente. Su CKAN 2.10 era una patch a `euro_dcat_ap.py` di ckanext-dcat; qui non serve toccare upstream, che mappa gia' `status` -> `adms:status` (`euro_dcat_ap_base.py`): bastava valorizzarlo.

## `2026-09-19` — Campi multilingua stampati come dict
- Alcuni cataloghi harvestati valorizzano i campi multilingua (es. `holder_name`) con un dict `{'en': '...'}`: la scheda dataset mostrava letteralmente `Nome: {'en': 'ATS della Montagna'}`. Aggiunto `helpers.localize_field_value()` (lingua corrente → it → en → primo valore), applicato in `couple_to_dict` e `couple_to_html`, cioe' in tutti i campi "accoppiati" della scheda (titolare, creatore, publisher…). Gestisce dict, JSON e repr Python; le stringhe normali restano invariate.

## `2026-09-19` — Etichetta DGA sui dataset ad accesso limitato
- I dataset con `dct:accessRights` RESTRICTED mostrano un badge **DGA** accanto al titolo (risultati di ricerca e pagina dataset), che linka alla ricerca filtrata. Helper `dcatita_is_restricted` / `dcatita_restricted_search_url` e snippet `snippets/dcatita_dga_badge.html` in ckanext-dcatita; override di `snippets/package_item.html` (blocco `heading_meta`) e `package/read.html` (blocco `page_heading`).

## `2026-09-13` — DataStore con tipi delle colonne
- Attivato `ckanext.xloader.use_type_guessing` (con `strict_type_guessing=false`: una colonna con celle sporche diventa `text` invece di far fallire l'intero typing) e alzato `ckan.max_resource_size`, da cui dipende `max_type_guessing_length` (default: 1/10). Il Data Dictionary non e' piu' tutto `text`: sul catalogo di collaudo 32 colonne `numeric` e 1 `timestamp` su 70.
- `use_type_guessing` agisce **solo alla creazione** della tabella DataStore: `xloader submit` su una risorsa gia' caricata non ritipizza. Per il pregresso c'e' `scripts/maintenance.sh xloader-retype [N]` (datastore_delete + submit, a scaglioni).
- Il percorso con tipi (tabulator) e' molto piu' lento del `COPY` diretto e rifiuta i CSV con righe piu' lunghe dell'intestazione: quelle risorse restano senza anteprima.

## `2026-09-13` — Fix post-esercizio
- dcatapit `IGroupForm.create_group_schema`: `default_group_schema` non esiste in 2.12 (`default_create_group_schema`): la creazione di organizzazioni/gruppi dava 500.
- ckanext-harvest: i consumer gather/fetch morivano ogni ~60 s con `redis.exceptions.TimeoutError: Timeout reading from socket` (BLPOP senza timeout) e venivano rilanciati da Compose. Patch `04_queue_redis_timeout.patch`: attesa a blocchi di 30 s e riconnessione automatica sugli errori di rete.

## `2026-09-13` — Badge MQA opzionale
- Il badge "Punteggio qualità dal portale europeo" (nel 2.10 era una copia intera di `package/read.html`) e' ora un override pulito in ckanext-dcatita (`templates/package/read.html`, blocchi `package_notes` e `scripts`), attivabile con `CKANEXT__DCATITA__MQA_BADGE=true`. Sensato solo per cataloghi harvestati da data.europa.eu.

## `2026-09-13` — Fix: commit negli hook (ResourceClosedError su package_update)
- CKAN 2.12 esegue gli hook `after_dataset_*`/`after_resource_*` dentro un SAVEPOINT di `package_update`; multilang (`PackageMultilang/GroupMultilang/ResourceMultilang.persist`) e la localizzazione tag di dcatapit facevano `Session.commit()` nell'hook, chiudendo la transazione esterna: `sqlalchemy.exc.ResourceClosedError: This transaction is closed` su qualunque salvataggio successivo nella stessa action (bulk privato/elimina dell'organizzazione, harvest, API). Ora fanno `flush()`; il commit resta all'action o al comando CLI chiamante (`ckan dcatapit load` committa gia' da solo).
- Stessa causa, altra forma: `DomainObject.save()`/`purge()` di CKAN fanno **commit**; dcatapit (`interfaces.py`) e multilang (`plugin.py`, `logic/package.py`, `logic/resource.py`) li usavano negli hook quando un campo localizzato cambiava. Sostituiti con `add/delete + flush`; i persist di multilang e `TagLocalization.persist` lavorano in un savepoint locale, cosi' un errore (es. chiave duplicata) annulla solo quello e non il salvataggio del dataset. Gli harvester multilang, che girano fuori dalle action, restano invariati.

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















