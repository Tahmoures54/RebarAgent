# License signing redesign and migration plan

**Status:** design proposal; not implemented. Do not treat this document as a security fix.

## Current trust-boundary defect

The desktop client contains SECRET_KEY used both to generate and verify HMAC activation keys. A user who can inspect the distributed executable can recover the shared secret and forge activation keys. The hidden-file HMAC key is also client-side, so it may detect accidental corruption but cannot provide a trustworthy anti-tamper boundary against a local administrator.

The current purchase path calls fulfill_paid_plan() from the desktop app and then calls issue_and_activate() locally. Simply replacing HMAC verification with public-key verification would break this flow because a client that only has a public key cannot issue signatures.

## Target design

1. **Signing authority:** private Ed25519 (or another vetted asymmetric scheme) key is generated and stored outside the repository, desktop package, logs, and user-accessible configuration. Prefer an offline issuer or a controlled license service. Never embed the private key in the client.
2. **Desktop verifier:** contains only the public verification key and a small verification routine. License payload includes a schema version, license ID, plan/SKU, machine binding, issued-at, expiry (or explicit perpetual flag), and key ID. Sign canonical serialized bytes; reject unknown schema/key IDs, invalid dates, wrong machine, and signature mismatch.
3. **Payment trust:** a license service should verify confirmed TRC20 USDT transfers, bind each transaction to one invoice/order, and atomically transition that order to fulfilled before issuing a license. The desktop must not have signing authority. If a service is not affordable/available, use an offline/manual issuer workflow and clearly disclose that automated local payment fulfillment is not a secure licensing boundary.
4. **Key rotation:** include a public key identifier (kid) so the verifier can temporarily trust a small set of public keys during rotation. Never fall back to the embedded legacy HMAC secret for newly issued licenses indefinitely.
5. **Local license file:** treat local storage as a cache of the signed license payload. A signature proves issuer authenticity, not that the user cannot roll back the local clock or copy/restore files. State those limits and decide whether periodic online revalidation is required.

## Migration policy

Do not silently reinterpret existing HMAC strings as asymmetric signatures.

- **Inventory first:** determine how many real customers/licenses exist and whether any legacy key must remain valid.
- **Preferred migration:** issue new signed licenses to verified purchasers through the new issuer. Preserve plan and expiry from trusted payment/issuance records, not values supplied by the client.
- **Legacy compatibility, if required:** put it behind a time-bounded, explicit migration mode. A legacy key can only be validated with the old secret, which remains extractable while that compatibility code ships. Document this as a temporary downgrade in security, set a removal release/date, and avoid using legacy acceptance to grant unlimited/perpetual access without a trusted record.
- **No customer base / no legacy keys:** remove legacy HMAC activation-key acceptance in a major or clearly announced release, and require all new keys to be signed by the external issuer.
- **Data migration:** existing local DB and hidden-file license fields are not themselves proof of a paid entitlement. Migration must not trust a locally editable license_type=unlimited field.

## Required implementation and tests

- Verify valid signature, reject altered payload/signature, unknown key ID, unsupported schema, expired license, wrong machine, malformed encoding, and non-canonical payload.
- Ensure the private key is not in Git history intended for release, package data, EXE strings, CI artifacts, or logs. A public key is safe to ship.
- Ensure issuance is impossible through the client verifier module.
- Verify that payment transaction IDs are globally unique at the trusted issuer using a database unique constraint and atomic state transitions.
- Test duplicate requests, concurrent fulfillment, process restart, provider timeout, and recovery after payment is confirmed but response delivery fails.
- Decide how offline users, machine replacement, refunds/chargebacks (if applicable), and key rotation are handled.
- Keep a rollback plan that does not re-enable client-side signing authority.

## Release gate

This proposal does not change application behavior. RA-SEC-001 and RA-PAY-001 remain OPEN / P0 until the target architecture is implemented, tested, and the legacy migration policy is approved. Do not publish a build claiming secure payment-backed licensing before those gates pass.
