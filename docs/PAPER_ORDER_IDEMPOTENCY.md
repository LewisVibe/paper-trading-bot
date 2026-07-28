# Paper-order idempotency contract

Every order-capable path must use `trading_bot.paper_orders.submit_paper_order`. The gateway refuses an order unless it is explicitly confirmed, paper-only, finite and positive, and carries a valid broker `client_order_id`.

Alpaca's current order API documents `client_order_id` as a unique identifier with a maximum length of 128 characters. Its idempotent-order guidance states that duplicate submissions using the same ID are rejected, preventing accidental double orders during retry logic.

## Client order IDs

`build_paper_order_client_order_id` derives an ID from:

- the audited route;
- a route-specific intent scope;
- normalized ticker;
- side;
- canonical quantity.

The intent is SHA-256 hashed. Raw intent text, credentials, account identifiers, and secrets are not included in the resulting ID.

Equal canonical intent produces the same ID. Changing any scoped field produces a different ID. IDs contain only ASCII letters, numbers, periods, underscores, and hyphens and are limited to 128 characters.

## Route scopes

| Route | Intent scope | Complementary duplicate protection |
| --- | --- | --- |
| Manual paper-order test | Current UTC hour | Existing open-order and recent matching-order checks |
| QQQ100 | Saved preview signal date | Position, open-order, and recent matching-order checks |
| Slow SMA | Calculated signal date | Position and open-order checks |
| Volatility-targeted growth | Existing saved ticket or automatic cycle ID | Saved execution state and recent client-ID checks |

The hourly manual scope provides a stable retry identity within a run window. Every manual paper order also performs a fail-closed recent matching-order lookback, so a matching closed order remains authoritative across adjacent windows. If recent order history cannot be read, the order is refused.

## Failure behavior

Before calling the broker, the gateway refuses:

- non-boolean confirmation or paper-mode values;
- malformed runtime field types;
- a missing or blank client order ID;
- leading or trailing whitespace;
- whitespace or control characters;
- non-ASCII or unsupported punctuation;
- IDs with no ASCII letter or number;
- more than 128 characters.

The gateway passes the validated ID directly into Alpaca's `MarketOrderRequest`. It never silently substitutes `None`.

## Verification

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_paper_order_gateway.py -p no:cacheprovider --basetemp .pilot3-pytest-tmp
.\.venv\Scripts\python.exe scripts\verify_paper_order_idempotency.py
.\.venv\Scripts\python.exe scripts\verify_repo_safety.py
```

These checks use mocks and static source inspection. They do not connect to Alpaca or submit paper orders.

## References

- [Alpaca Create an Order API](https://docs.alpaca.markets/us/reference/postorder)
- [Alpaca idempotent-order guidance](https://docs.alpaca.markets/us/docs/alpacas-cli)
