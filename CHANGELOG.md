# RebarAgent Changelog

## [1.6.1] – 2026-09-11 (Correctness & Iran-first hardening)
- **Cutting optimizer** now materializes the integer column-generation solution (was discarded, always FFD)
- **Scrap bank** keeps identical leftover bars as separate pieces instead of collapsing them
- **Confirm/rollback stock** uses the correct stock-row layout (5- and 6-column)
- **Migrations** no longer mark a failed schema change as complete
- **Sample project** uses real BS 8666 params (`L` / bent shapes 11 & 21) so lengths calculate
- **Lap splice** supports Mabhas 9, Eurocode 2, ACI 318, and n×db; dialog is wired to the calculator
- **Excel import** maps Persian headers, normalizes shape/standard codes, maps A→L for straight bars
- Splash/welcome/exports show **RebarAgent** and the real app version (was "AI Rebar v7.4")
- Listofer "Show All" filter works in Persian UI
- Doctor checks optimizer + Excel import; expanded automated tests

## [1.6.0] – First-win pack
- Sample project, Excel import/template, Savings report after Confirm

## [1.0.0] – 2026-08-27 (Rebrand & Foundation Improvements)
- Full rebrand AiRebar → **RebarAgent**; trial 14 days; themes Turquoise/Light/Dark

## [1.1.0] – Project Manager + Agent Insights
- `ui/project_manager.py`, `ui/agent_insights.py`, theme switcher

## [1.2.0] – Progress bar + packaging
- Determinate progress for cutting; pyproject.toml; build_exe.py

## [1.2.1] – Stability
- bbs_generator restore; exact demand packing; mip dependency; doctor.py

## [1.2.2] – E2E verified
- Shape short-code; qrcode/pillow; full headless E2E

## [1.3.0] – User psychology + i18n
- `utils/i18n.py` EN/FA; psychology-driven copy

## [1.3.1] – Full dialog i18n
- Input, Scrap, Stock, Cutting Plan EN/FA

## [1.4.0] – Commercial model
- REVENUE_PLANS Trial/Pro/Office/Lifetime; feature gates; purchase flow

## [1.4.1] – Pre-release hardening
- WhatsApp +989160684552; RELEASE checklist; version alignment

## [1.4.2] – Smart Stock Advisor
- Demand vs stock; order suggestions; apply into Stock

## [1.4.3] – Inventory on Confirm Plan
- Draft-safe optimize; Confirm applies scrap/stock changes

## [1.4.4] – Force Re-optimize rollback
- Inventory ledger; reverse used scraps, offcuts, stock deducts

## [1.5.0] – Competitive pack
- Dashboard, JSON backup, shortcuts, recent projects

## [1.5.1] – Backup restore + Recent projects

## [1.5.2] – Cutting optimizer upgrade
- Multi-length stock, kerf, min scrap, utilization metrics

## [1.5.3] – Comfort UX
- Coach strip, empty-state, toasts

## [1.5.4] – Agent brain layer
- `logic/agent_brain.py` health score + actions
