# Production Readiness Gates

This document records release gates that must be verified before describing RebarAgent as production-ready. A passing unit-test suite alone is not sufficient for licensing, payments, and inventory accounting.

## Current hardening work

- [x] Add Hypothesis property tests for cutting-plan validation.
- [x] Add Bandit and pip-audit to CI.
- [x] Parse BVBS XML with `defusedxml`.
- [x] Restrict scrap-manager SQL identifiers to fixed allowlists and bound user values.
- [x] Validate AI endpoint URL schemes; use HTTPS except for explicit loopback HTTP.
- [x] Restore the incomplete `logic/bbs_generator.py` implementation and cover its output with tests.
- [x] Serialize payment fulfillment within one running process to reduce duplicate-click/thread races.
- [ ] Obtain green CI on the final pull-request commit, including Windows build and dependency audit.
- [ ] Run a clean Windows executable smoke test on a machine without Python installed.

## P0 — Licensing trust boundary

The current desktop client contains the HMAC signing secret and can generate activation keys locally through `issue_and_activate`. A customer who extracts the application can reproduce the signing operation. The hidden-file HMAC secret is also embedded in the client and must not be presented as strong protection against a determined local attacker.

Required remediation:
1. Replace client-side shared-secret verification with an asymmetric signature such as Ed25519.
2. Embed only the public verification key in the customer application.
3. Keep the private signing key in a separate issuer tool or trusted service; never package it with the desktop application.
4. Separate payment confirmation from license issuance and document the legacy-key migration/revocation policy.
5. Test wrong keys, altered payloads, expiry boundaries, machine binding, malformed inputs, and legacy license behavior.

## P0 — Payment fulfillment

USDT payment matching and license issuance currently run in the desktop client. Used transaction IDs are stored in a local file, so the ledger is not shared across devices and is not a trusted global idempotency store. The in-process lock only prevents concurrent attempts in the same running process. The unique amount suffix can collide between different customers.

Before commercial release, use a trusted issuer/payment service or explicitly disable automatic self-service fulfillment until a secure operational process exists. A production implementation must provide globally unique transaction fulfillment, durable recovery after crashes, strict token/contract/recipient/amount/confirmation validation, and auditable handling of ambiguous payments.

## P1 — Inventory atomicity and idempotency

Cutting-plan inventory mutations currently span multiple committed operations. Compensating rollback is not atomic across process crashes, and replaying a stock-restoration ledger can duplicate stock. Conditional updates protect some individual mutations but do not make the entire operation transactional.

Required remediation:
1. Introduce a durable operation ID and operation ledger in SQLite.
2. Apply stock, scrap, and operation-state changes transactionally using one connection; avoid helper methods that commit internally inside the transaction.
3. Make confirm and revert idempotent, including recovery of operations left pending by a crash.
4. Add fault-injection tests for failures after each inventory mutation and for repeated confirm/revert calls.

## Release acceptance

Do not merge or publish solely because CI is green. The final release candidate must have:
- Green Linux tests, security scan, dependency audit, and Windows build on the exact same commit.
- A clean-install Windows smoke test covering launch, database initialization, BBS generation, export, license activation, and inventory confirm/revert.
- A documented backup/restore procedure for the local database.
- Explicitly resolved P0 items above or a consciously restricted release scope that disables the affected commercial/payment behavior.
