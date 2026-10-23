# Solr 9 con lo schema CKAN 2.12 + campi custom per dcatapit/multilang.
# Lo schema in setup/managed-schema e' lo schema ufficiale di CKAN 2.12.0
# (ckan/config/solr/schema.xml) con le sole aggiunte marcate "ckan-docker-ita".
#
# Base: immagine ufficiale solr (prima ckan/ckan-solr:2.12-solr9, ferma a Solr 9.9),
# con gli stessi passi di ckan/ckan-solr (configset `ckan` copiato da `_default`).
# Solr 9.10 corregge le vulnerabilita' di jetty/netty/jackson presenti nella 9.9;
# l'indice resta compatibile (stessa versione di Lucene), i volumi esistenti non
# vanno ricreati.
ARG SOLR_VERSION=9.10.1
FROM solr:${SOLR_VERSION}

EXPOSE 8983

ENV SOLR_CONFIG_DIR="/opt/solr/server/solr/configsets"
ENV SOLR_SCHEMA_FILE="$SOLR_CONFIG_DIR/ckan/conf/managed-schema"

USER root

# - aggiornamenti di sicurezza Ubuntu (openssl...)
# - moduli opzionali di Solr non usati da CKAN (estrazione documenti con Tika,
#   OpenNLP, cross-dc/Kafka, Hadoop, repository cloud...) e prometheus-exporter:
#   il configset `_default` non li carica; rimossi riducono la superficie e le
#   segnalazioni di vulnerabilita' delle librerie che si portano dietro.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /opt/solr/modules/* /opt/solr/prometheus-exporter \
    && cp -R $SOLR_CONFIG_DIR/_default $SOLR_CONFIG_DIR/ckan

ADD setup/managed-schema $SOLR_SCHEMA_FILE
RUN chmod 644 $SOLR_SCHEMA_FILE
USER solr

CMD ["sh", "-c", "solr-precreate ckan $SOLR_CONFIG_DIR/ckan"]
