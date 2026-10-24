#!/usr/bin/env python3
"""Charge a late fee on every overdue invoice and write a ledger entry."""
import datetime, psycopg2

FEE_CENTS = 1500
print(f"{datetime.datetime.now().isoformat()} apply_late_fees START", flush=True)
conn = psycopg2.connect("dbname=shopdb")
cur = conn.cursor()
cur.execute("SELECT id, account_id FROM invoices WHERE status = 'overdue' AND due_date < current_date")
rows = cur.fetchall()
for inv_id, acct in rows:
    cur.execute("UPDATE accounts SET balance_cents = balance_cents + %s WHERE id = %s", (FEE_CENTS, acct))
    cur.execute("INSERT INTO ledger (account_id, invoice_id, kind, amount_cents, created_at) VALUES (%s, %s, 'late_fee', %s, now())",
                (acct, inv_id, FEE_CENTS))
conn.commit()
print(f"{datetime.datetime.now().isoformat()} apply_late_fees END exit=0 charged={len(rows)}", flush=True)
