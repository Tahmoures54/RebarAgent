# Ed25519 license migration status

## Implemented on this branch

- Client activation keys use the versioned `v2.` envelope and Ed25519 signatures.
- The application contains only the Ed25519 public key; the signing private key is loaded only from `REBARAGENT_LICENSE_PRIVATE_KEY` on the issuer machine.
- The issuer fails closed when no private key is configured.
- Legacy HMAC activation keys are rejected, and key payloads, dates, license type, machine ID, and signatures are validated.
- Tests cover valid activation, legacy rejection, payload tampering, and missing issuer private key.

## Important release warnings

**Do not merge or publish this branch until the new public key and issuer private key have been securely provisioned and the migration is approved.** A matching private-key file was generated separately for the repository owner; it must not be committed, emailed, or packaged into the desktop executable. Store it in an encrypted offline backup and configure `REBARAGENT_LICENSE_PRIVATE_KEY` only on a trusted issuer machine. If this private key is lost, no further keys matching the committed public key can be issued. If it is exposed, treat the signing identity as compromised and rotate it.

The current desktop USDT checkout still discovers and validates payments on the client. Ed25519 prevents customers from forging signatures with the public key, but it does **not** make client-side payment validation trustworthy. A production release still requires a trusted payment/license service with durable, global transaction-idempotency and recovery. Until that exists, automatic self-service payment fulfillment must remain disabled in distributed builds.

Legacy HMAC activation keys will no longer activate after this migration. Existing customers need a controlled re-issuance/migration process before rollout; do not silently strand existing paid users.

The hidden-file HMAC secret remains client-side and is only a tamper-evidence convenience, not a security boundary against a local administrator.

## Verification checklist

- [ ] Confirm GitHub Actions passes on the PR head.
- [ ] Verify the built EXE contains no issuer private key or private-key environment value.
- [ ] Test a clean Windows installation, activation, expiry, machine mismatch, and malformed keys.
- [ ] Exercise customer migration from existing HMAC licenses.
- [ ] Replace client-side payment fulfillment with a trusted service before commercial release.
