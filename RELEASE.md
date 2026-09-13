# RebarAgent v1.6.2 – Release Notes

## Product
Offline desktop **Bar Bending Schedule (BBS)** + **1D cutting optimization** for detailers and site engineers.

- English UI (default) + full Persian i18n
- Iran-first commerce: **USDT TRC20 self-serve** in License Management (WhatsApp **+989160684552** only for problems)
- Trial / Pro / Office / Lifetime licensing

## What is included
- Multi-standard shape library (BS, ACI, EC2, Mabhas 9, …)
- Cutting optimizer: multi-stock lengths, kerf, min usable scrap; CG integer solution is used
- Smart inventory: Scrap Bank + Stock Manager; Confirm Plan + reversible ledger
- Lap splice: Mabhas 9 / Eurocode 2 / ACI 318
- Excel import with Persian headers
- Agent brain: health score, Insights, coach tips
- Sample project with bent shapes, Excel template, savings report
- Exports: Excel, PDF, HTML, BVBS
- Modular codebase (`logic/` + `ui/` split for maintainability)

## Install
```bash
git clone https://github.com/Tahmoures54/AiRebar.git RebarAgent
cd RebarAgent
python -m venv venv && source venv/bin/activate   # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```
Or: `pip install -e .` then `rebaragent`

## Build Windows EXE
```bash
pip install pyinstaller
python build_exe.py
# → dist/RebarAgent/
```

## Pre-ship checklist
- [x] `pytest tests/ -q`
- [x] APP_VERSION / pyproject = **1.6.2**
- [ ] Set `REBARAGENT_USDT_TRC20` or `payment.json` to your Tron USDT wallet before shipping
- [ ] WhatsApp sales number in config (fallback)
- [ ] Manual smoke on Windows: Sample → Cutting → Confirm → Export
- [ ] License dialog: pick plan → copy exact USDT amount (TronGrid mock or real 1-min wait)
- [ ] Optional: run `python tools/usdt_license_bot.py` on a VPS you control
- [ ] Change `REBARAGENT_LICENSE_SECRET` for production

## Do not ship
`*.db`, `logs/`, `license.dat`, customer data, default secret if customized

## Support
WhatsApp: +989160684552
