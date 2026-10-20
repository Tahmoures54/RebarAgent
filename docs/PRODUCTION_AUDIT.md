# RebarAgent Production Audit

**Audit started:** 2026-10-20  
**Repository:** `Tahmoures54/RebarAgent`  
**Baseline branch:** `main`  
**Baseline commit:** `86458c9571e972cc534a8190ba79c2501a183c91`  
**Audit branch:** `audit/production-hardening-2026-10`  
**Product version declared by README/pyproject:** `1.7.0`

> This is an evidence-based audit in progress, not a production approval. Findings below are based on files retrieved from the baseline commit. Runtime tests, a Windows clean-machine EXE run, and end-to-end payment verification have not yet been performed in this audit session.

## Executive decision

**NOT READY FOR PRODUCTION (provisional).** The source contains hard-coded HMAC signing secrets for license issuance/validation and a security-check method that unconditionally returns success. These are release-blocking findings until the trust model is redesigned or the release scope is explicitly changed. Payment and inventory claims also require runtime/integration evidence.

## Baseline evidence

| Item | Evidence |
|---|---|
| Default branch | `main` |
| Latest commit at audit start | `86458c9571e972cc534a8190ba79c2501a183c91` |
| Declared version | `1.7.0` in README.md and pyproject.toml |
| Desktop UI | Tkinter imports in `main.py` |
| Database | SQLite abstraction via `db.database.DatabaseManager` |
| Optimizer | PuLP / python-mip dependencies and `logic/optimizer.py` |
| Inventory | `logic/inventory_apply.py`, `ui/cutting_plan_db.py` |
| Payment | `utils/usdt_payment.py`, `ui/license_dialog.py`, optional `tools/usdt_license_bot.py` |
| Packaging | `build_exe.py` invokes PyInstaller |
| CI | `.github/workflows/tests.yml` runs pytest on Ubuntu/Python 3.11 |
| Test command documented | `PYTHONPATH=. python -m pytest tests/ -q` |

## Findings

### RA-SEC-001 — License signing secrets are embedded in source
- **Severity:** P0
- **Evidence:** `utils/license.py` defines `SECRET_KEY = b'AiRebar2025!SecretKeyForLicenseSigning'` and `HIDDEN_SECRET = b'AIREBAR_HIDDEN_FILE_SECRET_2025'`.
- **Impact:** A distributed desktop client contains the material used to sign activation keys and local license state. A determined user can extract these values from source or a packaged binary; HMAC does not provide authenticity when the signing secret is shipped to the verifier.
- **Reproduction:** Inspect the constants in `utils/license.py`; no runtime exploit is required to establish secret exposure.
- **Remediation:** Replace client-side shared-secret signing with asymmetric signatures: keep the private signing key outside the desktop client (offline issuer or controlled service) and ship only the public verification key. Define a migration strategy for already issued keys. Do not merely move the same secret to another bundled file.
- **Acceptance:** No signing private key or shared signing secret in source, history intended for distribution, or EXE; old-license migration is tested; tampered and forged keys are rejected.

### RA-SEC-002 — Startup security gate always passes
- **Severity:** P1 (promote to P0 if this gate is relied on for a mandatory security invariant)
- **Evidence:** `main.py`, `RebarAgentApp._run_security_checks()` returns `True` unconditionally.
- **Impact:** The method gives the appearance of a security gate without enforcing any checks.
- **Reproduction:** Read the method; every invocation returns true.
- **Remediation:** Remove the misleading gate if it has no defined security contract, or implement and test only concrete checks. Never treat it as proof that the application is secure.
- **Acceptance:** Each retained check has a documented invariant and positive/negative tests.

### RA-PAY-001 — Desktop payment fulfillment and license issuance need stronger trust-boundary review
- **Severity:** P0
- **Evidence:** `utils/usdt_payment.py` documents that the desktop app matches incoming transfers and issues a license without a backend. `utils/license.py` contains the shared signing secret. README directs users to press “I paid” and the desktop app to activate automatically.
- **Impact:** On-chain transfer matching can establish payment facts, but the desktop client cannot safely hold a license-signing secret. Unique amount suffixes also have a documented collision possibility (10–99 cents), so amount alone is not a globally unique invoice identifier.
- **Remediation:** Separate payment verification from license issuance. Keep signing authority outside the client; bind a payment transaction to one invoice/order using durable unique constraints and atomic state transitions. If no trusted issuer is available, disclose the limitation and do not claim secure self-serve licensing.
- **Acceptance:** Mock tests cover wrong recipient, amount, token/contract, age/confirmation status, duplicate TXID, concurrent fulfillment, network errors and recovery; issuer key is never present in client artifacts.

### RA-INV-001 — Inventory apply/revert requires atomicity and concurrency verification
- **Severity:** P1
- **Evidence:** `logic/inventory_apply.py` applies mutations across scrap and stock and records mutation lists for compensating rollback. The source comments describe rollback-on-error, but comments alone do not prove database-level atomicity.
- **Impact:** A process crash or concurrent operation could leave stock, scrap and ledger state inconsistent unless all changes share a transaction and appropriate constraints.
- **Remediation:** Trace database connection/transaction boundaries through model methods and plan confirmation. Add failure-injection, repeated-confirm, repeated-rollback and concurrency tests against a temporary database.
- **Acceptance:** Tests prove all-or-nothing behavior and no duplicate consumption under retries.

### RA-OPT-001 — Cutting optimizer needs independent physical-result validation
- **Severity:** P1
- **Evidence:** Optimizer implementation is split across `logic/optimizer.py` and supporting modules; dependencies include PuLP and python-mip. Existing test coverage must be executed and reviewed before the result can be certified.
- **Impact:** A solver status alone does not prove the returned cutting pattern respects demand, stock capacity, kerf and inventory constraints.
- **Remediation:** Validate each generated solution independently before display or persistence; add deterministic hand-calculated cases and bounded generated cases.
- **Acceptance:** Invalid/infeasible/partial solver results are rejected; repeated inputs produce valid, reproducible physical plans.

### RA-BUILD-001 — Windows packaging is not yet independently verified
- **Severity:** P1
- **Evidence:** `build_exe.py` invokes PyInstaller with hidden imports and bundles `app_config.json` and `User_Guide.html` if present. The script itself does not prove the produced EXE runs without Python or that writable data paths are safe.
- **Impact:** Packaging may omit dynamic imports/resources or depend on development-machine state.
- **Remediation:** Build on Windows CI, retain artifacts, and run smoke tests on a clean Windows environment with a non-ASCII path and no Python installed.
- **Acceptance:** The EXE launches, calculates, persists data, exports files, and survives restart on a clean Windows host.

### RA-CI-001 — CI currently tests one Linux/Python combination
- **Severity:** P2
- **Evidence:** `.github/workflows/tests.yml` uses Ubuntu and Python 3.11 and runs pytest. README states Python 3.9+.
- **Impact:** Windows-specific packaging/runtime failures and compatibility claims for other Python versions are not covered by this workflow.
- **Remediation:** Add Windows packaging/smoke coverage and align the supported Python range with actually tested environments. Add dependency vulnerability checks without secrets.
- **Acceptance:** The final commit has successful CI evidence and a retained Windows build artifact.

## Test / evidence status

| Check | Status | Evidence / reason |
|---|---|---|
| Repository metadata and default branch | PASS | GitHub repository search reports public repo and default branch `main`. |
| Baseline commit identified | PASS | Latest commit search returned `86458c9571e972cc534a8190ba79c2501a183c91`. |
| Hard-coded license secrets reviewed | PASS (finding confirmed) | `utils/license.py` retrieved from baseline. |
| Always-true security gate reviewed | PASS (finding confirmed) | `main.py` retrieved from baseline. |
| Full pytest suite | PASS on CI (Linux and Windows) | Runs `39491053255` and `39491085635`; see the follow-up evidence section. |
| Payment integration tests against live network | NOT RUN | No live payments will be used; controlled mocks are required. |
| Windows EXE build | PASS (build only) | Run `39491085635` built the EXE and verified its expected path. |
| Clean Windows EXE smoke test | NOT RUN | CI verifies build and artifact existence only; no clean-machine launch/functional test has been done. |
| GitHub Actions run for audit candidate | PASS for tested code commit | Run `39491085635` passed on `7bfe9a4fa38a7525045e8cc2e766cf105d2abf12`; subsequent documentation-only commit is not represented by that run. |

## Release gates still open

1. Replace the client-embedded license signing secret with a public-key verification design and document legacy key migration.
2. Remove or implement the unconditional startup security gate.
3. Prove payment fulfillment idempotency and durable duplicate-TXID protection under concurrent calls and process interruption.
4. Prove inventory apply/rollback atomicity and physical cutting-plan validity with executed tests.
5. Execute the full test suite on the candidate commit.
6. Build and smoke-test the Windows EXE; do not infer success from the build script.
7. Verify dependencies/secrets and reconcile README/RELEASE checklists with actual evidence.

**No production approval is implied by this document. Update every status only after collecting corresponding evidence.**


## Follow-up remediation log — 2026-10-20

### RA-SEC-002 update
- **Change:** `main.py` now runs SQLite `PRAGMA quick_check` and `PRAGMA foreign_key_check` before opening the main window. Failed checks and database exceptions stop startup and show a user-facing error.
- **Test added:** `tests/test_startup_integrity.py` covers a healthy in-memory database, a closed/broken connection, and a failed quick check.
- **Commit:** `af2f99bf5776098eb49cf9f80c27ccf9c65e152e` (implementation); `198a1d17a4437fd376b204f1b19d70c5ffee2bad` (tests).
- **Execution status:** NOT RUN in a local Python runtime. GitHub Actions is the evidence path; its result must be checked before treating the tests as PASS.
- **Scope caveat:** This is a database integrity gate, not a security guarantee. It does not resolve RA-SEC-001 or the payment trust-boundary risks.

### Current critical status
RA-SEC-001 remains **OPEN / P0**: client-bundled HMAC signing secrets remain in `utils/license.py`. Do not ship a new production build until a compatible public-key verification design and license migration plan are implemented and tested.


## Follow-up — payment token metadata fail-closed fix (2026-10-20)

- **Code change:** `utils/usdt_payment.py::match_payment` now requires an exact match for `USDT_TRC20_CONTRACT` and the `USDT` symbol. Missing contract/symbol metadata no longer passes the token checks.
- **Regression test added:** `tests/test_usdt_checkout.py::test_match_payment_rejects_missing_or_wrong_token_metadata` verifies that missing contract, missing symbol, a wrong symbol, and a wrong contract are rejected.
- **Implementation commit:** `9bec523f9b9613ad0cc6ccb8121bf874061322c4`
- **Test commit:** `412d5309bee2a18a18a899cfcd99111386248f12`
- **CI status:** Run for the implementation commit was in progress at the time of this update. The test commit's CI result must be checked before considering this change verified.
- **Scope limit:** This is only a fail-closed token metadata correction. It does not solve desktop-side license signing secrets, durable atomic TXID consumption, payment order identity/collision risks, or Windows release validation.
- **Release decision:** **NOT READY FOR PRODUCTION**.


## Follow-up — CI and Windows packaging evidence (2026-10-20)

- **Windows CI:** Successful run `39491085635` for commit `7bfe9a4fa38a7525045e8cc2e766cf105d2abf12`. Both `pytest` and `windows-build` jobs passed.
- **Packaging evidence:** The Windows job successfully ran `python build_exe.py`, verified `dist/RebarAgent/RebarAgent.exe` exists, and uploaded the `RebarAgent-Windows-Python311` artifact (14-day retention).
- **Linux CI:** Successful run `39491053255` for commit `e85cbd6fe1a0498bb63972a8054dbedbd59dd38d`; both `pytest` and `windows-build` jobs passed for that commit's workflow configuration.
- **Console encoding fix:** `build_exe.py` now prints an ASCII-only success message to avoid a Windows console encoding error after packaging. Commit: `e85cbd6fe1a0498bb63972a8054dbedbd59dd38d`.
- **Artifact workflow:** Commit `7bfe9a4fa38a7525045e8cc2e766cf105d2abf12` adds upload-artifact after the executable existence check.
- **Links:** [Windows build + artifact run](https://github.com/Tahmoures54/RebarAgent/actions/runs/39491085635); [encoding-fix run](https://github.com/Tahmoures54/RebarAgent/actions/runs/39491053255).
- **Remaining limitation:** This proves the build completes and the expected EXE path exists; it does **not** prove the EXE launches or functions on a clean Windows machine. Clean-machine runtime smoke tests, non-ASCII path checks, database persistence, optimization, and exports remain open.
- **Current release decision:** **NOT READY FOR PRODUCTION**. The embedded HMAC signing secret and payment idempotency/trust-boundary issues remain release blockers.


### RA-OPT-001 update — independent validator foundation (2026-10-20)

- **Change:** Added `logic/optimizer_validation.py` with a solver-independent check for exact requested piece-length multiplicity, invalid/non-finite lengths, and per-bar capacity after kerf.
- **Tests:** Added `tests/test_optimizer_validation.py` for valid plans, missing/duplicate demand, kerf capacity overflow, non-physical lengths, and invalid kerf.
- **Documentation:** `docs/OPTIMIZER_VALIDATION.md` records scope, limitations, and integration gates.
- **Linux CI:** Run `39492003887` pytest job passed on code SHA `227d282b3d31fdc3eb04709ff25d266ce2af8c22`.
- **Windows CI:** The Windows build job for that run was still in progress when this report was updated; do not infer its result.
- **Important limitation:** The validator is a tested helper but is not yet wired into all optimizer output/display/persistence paths. RA-OPT-001 remains OPEN and this change alone does not certify cutting plans for production.


### RA-SEC-001 / RA-PAY-001 update — migration design documented (2026-10-20)

- **Change:** Added docs/LICENSE_SIGNING_REDESIGN.md describing the asymmetric-signature target, external signing authority, payment trust boundary, key rotation, legacy migration choices, and required acceptance tests.
- **Code status:** No licensing/payment behavior was changed in this step; the embedded HMAC secrets and client-side issuance path remain.
- **Decision:** RA-SEC-001 and RA-PAY-001 remain OPEN / P0. This is a design artifact, not remediation or production approval.
