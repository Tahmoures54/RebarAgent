# RebarAgent v1.7.0 – Release Notes

## Product
Offline desktop **Bar Bending Schedule** + **1D cutting** with a local Copilot (health score, next action, leftover coaching). Iran-first sales: USDT TRC20 in-app.

## Ship checklist
- [x] `pytest tests/ -q`
- [x] APP_VERSION / pyproject = **1.7.0**
- [ ] Copy `.env.example` → `.env` and set:
  - `REBARAGENT_USDT_TRC20`
  - `REBARAGENT_WORKER_URL` (Telegram bot or landing)
  - `REBARAGENT_TELEGRAM_BOT_TOKEN` if you run the bot
  - plan prices `REBARAGENT_PRICE_*_USD` / `_IRR`
- [ ] Manual smoke on Windows: Sample → Cutting → Confirm → HTML listofer (footer ad visible)
- [ ] Change license signing secret for production

## Do not ship
`.env`, `*.db`, `logs/`, `license.dat`, customer data

## Support
WhatsApp from `.env` (`REBARAGENT_WHATSAPP`, default +989160684552)
