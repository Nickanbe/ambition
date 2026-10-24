# ingest

Small helpers the nightly import job uses to read CSV exports from billing.

```
python -m ingest summary data/payments.csv
python -m ingest head data/payments.csv -n 3
```

Run the tests with `python -m unittest discover -s tests -t .`
