# RebarAgent – Intelligent Bar Bending Schedule & Cutting Optimization

**Version 1.7.0** | Desktop BBS + Copilot cutting for detailers and site teams

RebarAgent is a professional **offline-first** desktop app for civil/structural engineers and rebar detailers. Create Bar Bending Schedules, optimize 1D cutting with multi-stock lengths, manage scrap and stock inventory, and export Excel / PDF / HTML / BVBS.

Repository: https://github.com/Tahmoures54/AiRebar

## Highlights (v1.7.0)

- **Copilot** – health score on the KPI strip, next action, duplicate-mark catch, 6 m vs 12 m advice
- **Cutting optimizer** – multi-length stock, kerf, min usable scrap; column-generation result is actually applied
- **Smart inventory** – Scrap Bank + Stock Manager; identical offcuts stay as separate bars; Confirm/rollback stock is reliable
- **Print HTML** – A4 listofer and cutting reports with Copilot strip and RebarAgent footer (WhatsApp / worker)
- **Lap splice** – Mabhas 9, Eurocode 2, ACI 318, and site n×db rule
- **Excel import** – English + Persian column headers, shape/standard aliases
- **i18n** – English (default) + Persian
- **Commercial** – USDT TRC20 self-serve; prices and wallet from `.env`

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

Copy `.env.example` → `.env` and set wallet, worker URL, and plan prices. The app and `tools/usdt_license_bot.py` read them at start.

```bash
cp .env.example .env
# fill REBARAGENT_USDT_TRC20, REBARAGENT_WORKER_URL, REBARAGENT_TELEGRAM_BOT_TOKEN, prices
```

In **License Management** the customer picks a plan, sends the **exact USDT TRC20 amount**, taps **I paid**. WhatsApp is only for problems.

```bash
python tools/usdt_license_bot.py   # optional 24/7 Telegram seller on your VPS
```

Send **only TRC20**. See `CHANGELOG.md` and `RELEASE.md`.
