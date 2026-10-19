# ocracy.catalog

### ocracy.catalog *= <Catalog 64 backends | 15 implemented | 40 local, 38 remote>*

[`ocracy.kit.ledger.Catalog`](ocracy.kit.ledger.html.md#ocracy.kit.ledger.Catalog) bound to ocracy’s data.

Loaded lazily from `DEFAULT_LEDGER_PATH` (override via the `path`
argument or the `OCRACY_LEDGER` environment variable). `filter()`
returns a *new* `Catalog` over the matching subset, so filters compose:

```default
catalog.filter(is_remote=True).filter(pricing_model="free_tier_then_paid")
```

* **Type:**
  ocracy’s ledger
