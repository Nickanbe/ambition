# billing

Cart math and invoices for the shop backend.

```python
from billing import LineItem, calc_total
calc_total([LineItem("MUG-01", Decimal("12.50"), 2)], tax_rate=Decimal("0.08"))
```

`calc_total` applies the discount before tax and rounds once, to cents.

Tests: `python -m unittest discover -s tests -t .`
