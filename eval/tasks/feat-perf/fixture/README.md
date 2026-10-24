# contacts

Merges duplicate contact records from our CRM exports (one row per signup,
event scan, import...) into one record per email address.

```
python -m contacts data/sample.json merged.json
```

Tests: `python -m unittest discover -s tests -t .`
