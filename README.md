# RebarAgent – Intelligent Bar Bending Schedule & Cutting Optimization

**Version 1.6.2** | Desktop BBS + smart cutting for detailers and site teams

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
- **Commercial** – Trial / Pro / Office / Lifetime; pay USDT (TRC20) in License Management for automatic activation (WhatsApp only if something fails)

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

Commercial / trial model. In **License Management** the customer picks a plan, sends the **exact USDT TRC20 amount** shown, taps **I paid**, and the app activates itself.

Before you ship a build, set your Tron receive wallet once:

```bash
# option A — environment (also used by the optional Telegram bot)
export REBARAGENT_USDT_TRC20=TYourTronAddress...

# option B — file next to the app / repo (copy and edit)
cp payment.json.example payment.json
```

Optional 24/7 Telegram seller (run on a VPS you control, not a Cursor worker):

```bash
export REBARAGENT_TELEGRAM_BOT_TOKEN=123:abc
export REBARAGENT_USDT_TRC20=TYourTronAddress...
python tools/usdt_license_bot.py
```

Send **only TRC20**. Wrong network cannot be recovered. WhatsApp **+989160684552** remains for payment problems.

See `CHANGELOG.md` and `RELEASE.md` for full history and release checklist.
