# report

Revenue by customer from the orders export.

```
python -m report data/orders.csv
python -m report data/orders.csv --region EU --since 2026-08-01
```

Tests: `python -m unittest discover -s tests -t .`
