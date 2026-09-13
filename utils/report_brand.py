# utils/report_brand.py
"""Shared print branding: customer header + RebarAgent footer advertisement."""

from __future__ import annotations

import html as html_mod
from typing import Optional

from config import APP_NAME, APP_VERSION, PURCHASE_CONTACT


BRAND = {
    "name": APP_NAME,
    "color": "#0f766e",
    "color_dark": "#134e4a",
    "ink": "#0f172a",
    "muted": "#64748b",
    "paper": "#f8fafc",
    "tagline_en": "Intelligent listofer · less waste · site-ready print",
    "tagline_fa": "لیستوفر هوشمند · پرت کمتر · آمادهٔ کارگاه",
    "pitch_en": "Generated with RebarAgent — cutting optimization, scrap bank, and a schedule the crew can trust.",
    "pitch_fa": "تهیه‌شده با RebarAgent — بهینه‌سازی برش، بانک ضایعات، لیستوفری که اکیپ می‌تواند به آن اعتماد کند.",
}


def sales_whatsapp_url() -> str:
    digits = "".join(ch for ch in (PURCHASE_CONTACT.get("whatsapp") or "") if ch.isdigit())
    return f"https://wa.me/{digits}" if digits else "#"


def sales_worker_url() -> str:
    return (PURCHASE_CONTACT.get("worker_url") or PURCHASE_CONTACT.get("telegram_url") or "").strip()


def sales_website() -> str:
    return (PURCHASE_CONTACT.get("website") or "https://github.com/Tahmoures54/RebarAgent").strip()


def page_css() -> str:
    c = BRAND["color"]
    d = BRAND["color_dark"]
    return f"""
    <style>
    @page {{ size: A4; margin: 12mm 12mm 16mm 12mm; }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
        font-family: 'Segoe UI', 'Vazirmatn', Tahoma, Arial, sans-serif;
        background: #e2e8f0;
        color: {BRAND["ink"]};
        line-height: 1.5;
        display: flex;
        justify-content: center;
        padding: 24px 12px 48px;
    }}
    .page {{
        max-width: 210mm;
        width: 100%;
        background: #fff;
        padding: 14mm 14mm 12mm;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
        border-radius: 10px;
    }}
    .report-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 14px; border-bottom: 3px solid {c}; margin-bottom: 16px; gap: 16px;
    }}
    .company-name {{ font-size: 22px; font-weight: 800; color: {d}; letter-spacing: -0.02em; }}
    .header-title {{ font-size: 15px; font-weight: 650; color: #334155; }}
    .header-subtitle {{ font-size: 12px; color: {BRAND["muted"]}; }}
    .qr-code svg {{ width: 58px; height: 58px; }}
    .project-info {{
        background: linear-gradient(135deg, #f0fdfa 0%, {BRAND["paper"]} 100%);
        border: 1px solid #ccfbf1; border-radius: 12px; padding: 14px 18px;
        display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 18px;
    }}
    .project-info .label {{ font-weight: 700; color: {d}; }}
    .ai-strip {{
        display: flex; gap: 14px; align-items: flex-start;
        background: {d}; color: #ecfeff; border-radius: 12px; padding: 12px 16px; margin: 0 0 20px;
    }}
    .ai-score {{
        min-width: 72px; text-align: center; background: {c}; border-radius: 10px; padding: 8px 6px;
        font-weight: 800; font-size: 20px; line-height: 1.1;
    }}
    .ai-score small {{ display: block; font-size: 10px; font-weight: 600; opacity: 0.85; }}
    .ai-strip p {{ font-size: 13px; margin: 0; }}
    .ai-strip .kicker {{ font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.75; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; margin: 12px 0 18px; }}
    th {{ background: {d}; color: #fff; padding: 9px 6px; font-weight: 650; text-align: center; }}
    td {{ padding: 7px 5px; border-bottom: 1px solid #e2e8f0; text-align: center; vertical-align: middle; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 18px 0; }}
    .summary-card {{ background: {BRAND["paper"]}; border-radius: 12px; padding: 14px; border: 1px solid #e2e8f0; }}
    .summary-card .value {{ font-size: 26px; font-weight: 800; color: {d}; }}
    .summary-card .label {{ font-size: 11px; color: {BRAND["muted"]}; text-transform: uppercase; letter-spacing: 0.06em; }}
    .signatures {{ margin-top: 28px; padding-top: 18px; border-top: 2px solid {c}; display: flex; justify-content: space-between; }}
    .signature-box {{ width: 46%; text-align: center; }}
    .signature-line {{ margin: 40px 0 8px; border-bottom: 1px solid #334155; }}
    .ad-footer {{
        margin-top: 28px; padding: 16px 18px; border-radius: 14px;
        background: linear-gradient(120deg, {d} 0%, {c} 100%);
        color: #f0fdfa; display: flex; justify-content: space-between; align-items: center; gap: 16px;
        page-break-inside: avoid;
    }}
    .ad-footer strong {{ font-size: 15px; }}
    .ad-footer p {{ font-size: 12px; opacity: 0.92; margin-top: 4px; max-width: 420px; }}
    .ad-footer .cta a {{
        display: inline-block; background: #fff; color: {d}; font-weight: 800; font-size: 12px;
        text-decoration: none; padding: 8px 12px; border-radius: 999px; margin: 4px 0 0 8px;
    }}
    @media print {{
        body {{ background: #fff; padding: 0; display: block; }}
        .page {{ box-shadow: none; border-radius: 0; margin: 0; padding: 0; max-width: none; }}
        .ad-footer {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
    </style>
    """


def copilot_strip_html(score: Optional[int], headline: str, lang: str = "en") -> str:
    if score is None and not headline:
        return ""
    kicker = "RebarAgent Copilot" if lang != "fa" else "کوپایلت RebarAgent"
    score_txt = "—" if score is None else str(int(score))
    return f"""
    <aside class="ai-strip">
      <div class="ai-score">{html_mod.escape(score_txt)}<small>/100</small></div>
      <div>
        <div class="kicker">{html_mod.escape(kicker)}</div>
        <p>{html_mod.escape(headline or "")}</p>
      </div>
    </aside>
    """


def footer_html(lang: str = "en") -> str:
    pitch = BRAND["pitch_fa"] if lang == "fa" else BRAND["pitch_en"]
    wa = sales_whatsapp_url()
    site = sales_website()
    worker = sales_worker_url()
    worker_btn = ""
    if worker:
        label = "خرید / پشتیبانی" if lang == "fa" else "Buy / support"
        worker_btn = f'<a href="{html_mod.escape(worker)}">{html_mod.escape(label)}</a>'
    wa_label = "واتساپ" if lang == "fa" else "WhatsApp"
    web_label = "وب" if lang == "fa" else "Web"
    brand = html_mod.escape(BRAND["name"])
    ver = html_mod.escape(APP_VERSION)
    return f"""
    <footer class="ad-footer">
      <div>
        <strong>{brand} v{ver}</strong>
        <p>{html_mod.escape(pitch)}</p>
      </div>
      <div class="cta">
        <a href="{html_mod.escape(wa)}">{html_mod.escape(wa_label)}</a>
        <a href="{html_mod.escape(site)}">{html_mod.escape(web_label)}</a>
        {worker_btn}
      </div>
    </footer>
    """
