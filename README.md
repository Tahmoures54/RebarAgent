# RebarAgent – Intelligent Bar Bending Schedule & Cutting Optimization

**Version 1.6.1** | Desktop BBS + smart cutting for detailers and site teams

RebarAgent is a professional **offline-first** desktop app for civil/structural engineers and rebar detailers. Create Bar Bending Schedules, optimize 1D cutting with multi-stock lengths, manage scrap and stock inventory, and export Excel / PDF / HTML / BVBS.

Repository: https://github.com/Tahmoures54/AiRebar

## Highlights (v1.6.1)

- **Cutting optimizer** – multi-length stock, kerf, min usable scrap; column-generation result is actually applied
- **Smart inventory** – Scrap Bank + Stock Manager; identical offcuts stay as separate bars; Confirm/rollback stock is reliable
- **Lap splice** – Mabhas 9, Eurocode 2, ACI 318, and site n×db rule
- **Excel import** – English + Persian column headers, shape/standard aliases
- **Agent brain** – health score, prioritized tips, one-click actions, Insights panel
- **First-win UX** – sample project with bent bars, Excel template, coach strip, savings report
- **i18n** – English (default) + Persian (including “Show All” filter)
- **Commercial** – Trial / Pro / Office / Lifetime; WhatsApp purchase (+989160684552)

## Quick start

```bash
git clone https://github.com/Tahmoures54/AiRebar.git RebarAgent
cd RebarAgent
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Or: `pip install -e .` then `rebaragent`

## Main workflow

1. **New / Open project** (or **Load Sample Project**)
2. **Add positions** (New Pos) or **Import from Excel**
3. Set **Stock** (6 m / 12 m bars) and optional scraps
4. **Cutting Plan** → review waste → **Confirm Plan** → savings report
5. Export Excel / PDF / HTML / BVBS

## Requirements

Python 3.9+ · pandas · openpyxl · reportlab · numpy · PuLP · mip · svgwrite · qrcode · pillow · tkinter

## Structure

```
main.py, config.py, app_state.py
db/          SQLite
logic/       calculator, optimizer, inventory, agent_brain, sample_project
shapes/      multi-standard library
ui/          Tkinter windows
utils/       i18n, export, license, excel_import, project_backup
tests/
```

## Packaging

```bash
pip install pyinstaller
python build_exe.py   # → dist/RebarAgent/
```

## License & sales

Commercial / trial model. In-app License Management or WhatsApp **+989160684552**.

See `CHANGELOG.md` and `RELEASE.md` for full history and release checklist.
