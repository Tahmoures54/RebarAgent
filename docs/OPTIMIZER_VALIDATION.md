# Independent cutting-plan validation — implementation note

## Scope

The function `logic.optimizer_validation.validate_labeled_cutting_plans` is a solver-independent validation helper for the optimizer's labeled-plan shape. It checks:

- every requested cut length is represented with the same multiplicity in the result;
- no unexpected/duplicate piece lengths are returned;
- lengths and bar capacities are finite and positive;
- effective length (piece length plus kerf per piece) does not exceed each plan's bar capacity.

It returns a list of errors instead of raising, so callers can log all detected defects and fail closed.

## Important limitations

- Demand matching is by length multiplicity, not label identity. The optimizer may use labels for position/diameter/grade; those invariants must be checked by the caller where relevant.
- Kerf is charged once per piece, conservatively, matching the current optimizer helper convention. Confirm that convention against the actual saw/cut-count model before release.
- This helper is not yet wired into every optimization/display/persistence path. Its tests establish a foundation, **not production acceptance**.
- It does not prove inventory availability, scrap ownership, solver optimality, or database atomicity.

## Next integration gates

1. Identify every call site of optimize_labeled_cuts, optimize_with_scraps_and_stock, and store_cutting_assignments.
2. Validate results at a shared boundary before UI display and again before persistence, supplying the exact demand and kerf used for that run.
3. Reject invalid plans with a user-visible actionable error; do not silently replace or persist them.
4. Add tests for multi-stock groups, scrap bars, rounding boundaries, cancellation/partial solver output, and persistence rejection.
5. Run the full Linux and Windows CI suites on the final code SHA.
