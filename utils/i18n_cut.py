# utils/i18n_cut.py
"""Extra cutting-plan and critical-error strings (EN/FA)."""


def register(strings: dict) -> None:
    strings.setdefault("en", {}).update({
        "cut.generate": "Generate / Optimize",
        "cut.export_html": "Export HTML",
        "cut.no_plan": "No plan to confirm.",
        "cut.apply_inventory": "Apply this plan to inventory (scrap/stock)?",
        "cut.confirmed_title": "Confirmed",
        "cut.inventory_updated": "Inventory updated.",
        "cut.confirmed_summary": "Confirmed. Stock bars used: {n}",
        "cut.revert_ask": "Revert inventory and re-run optimizer?",
        "cut.revert": "Revert",
        "cut.no_export": "No plan to export.",
        "cut.export_saved": "Saved:\n{path}",
        "cut.pulp_missing": "PuLP is not installed. Run: pip install pulp",
        "cut.optimization": "Optimization",
        "cut.status_summary": "Status: {status}  |  bars: {bars}  |  waste: {waste:.2f} m",
        "err.critical": "A critical error occurred. Check the log file.",
        "err.system": "System Error",
    })
    strings.setdefault("fa", {}).update({
        "cut.generate": "تولید / بهینه‌سازی",
        "cut.export_html": "خروجی HTML",
        "cut.no_plan": "برنامه‌ای برای تأیید وجود ندارد.",
        "cut.apply_inventory": "این برنامه روی موجودی (ضایعات / انبار) اعمال شود؟",
        "cut.confirmed_title": "تأیید شد",
        "cut.inventory_updated": "موجودی به‌روز شد.",
        "cut.confirmed_summary": "تأیید شد. تعداد شاخه مصرف‌شده: {n}",
        "cut.revert_ask": "موجودی برگردانده شود و بهینه‌ساز دوباره اجرا شود؟",
        "cut.revert": "بازگردانی",
        "cut.no_export": "برنامه‌ای برای خروجی وجود ندارد.",
        "cut.export_saved": "ذخیره شد:\n{path}",
        "cut.pulp_missing": "کتابخانه PuLP نصب نیست. دستور: pip install pulp",
        "cut.optimization": "بهینه‌سازی",
        "cut.status_summary": "وضعیت: {status}  |  شاخه: {bars}  |  پرت: {waste:.2f} m",
        "err.critical": "خطای جدی رخ داد. فایل لاگ را بررسی کنید.",
        "err.system": "خطای سیستم",
    })
