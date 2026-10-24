#!/bin/bash
# Recompute products.search_vector and refresh the search materialized view.
set -euo pipefail
echo "$(date -Is) rebuild_search_index START"
psql shopdb -v ON_ERROR_STOP=1 <<SQL
BEGIN;
UPDATE products SET search_vector = to_tsvector('english', name || ' ' || coalesce(description, ''));
REFRESH MATERIALIZED VIEW product_search;
COMMIT;
SQL
echo "$(date -Is) rebuild_search_index END exit=$?"
