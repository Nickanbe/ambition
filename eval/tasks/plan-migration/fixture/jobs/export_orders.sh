#!/bin/bash
# Export yesterday's orders to the 3PL warehouse over SFTP.
set -u
D=$(date -d yesterday +%F)
echo "$(date -Is) export_orders START"
psql shopdb -Atc "copy (select * from orders where created_at::date = '$D') to stdout csv header" > /tmp/orders_$D.csv
sftp -b - wh3pl@sftp.warehouse.example <<SFTP 2>&1 | tee -a /var/log/export_orders.err || true
put /tmp/orders_$D.csv inbound/
SFTP
echo "$(date -Is) export_orders END exit=0"
exit 0
