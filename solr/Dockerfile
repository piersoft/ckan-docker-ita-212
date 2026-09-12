# Solr 9 con lo schema CKAN 2.12 + campi custom per dcatapit/multilang.
# Lo schema in setup/managed-schema e' lo schema ufficiale di CKAN 2.12.0
# (ckan/config/solr/schema.xml) con le sole aggiunte marcate "ckan-docker-ita".
FROM ckan/ckan-solr:2.12-solr9

EXPOSE 8983

ENV SOLR_CONFIG_DIR="/opt/solr/server/solr/configsets"
ENV SOLR_SCHEMA_FILE="$SOLR_CONFIG_DIR/ckan/conf/managed-schema"

USER root
ADD setup/managed-schema $SOLR_SCHEMA_FILE
RUN chmod 644 $SOLR_SCHEMA_FILE
USER solr

CMD ["sh", "-c", "solr-precreate ckan $SOLR_CONFIG_DIR/ckan"]
