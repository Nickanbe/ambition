#!/bin/bash
# Remove export files older than 7 days.
echo "$(date -Is) cleanup_tmp START"
find /tmp -maxdepth 1 -name 'orders_*.csv' -mtime +7 -delete
echo "$(date -Is) cleanup_tmp END exit=0"
