# utils/html_report.py
"""
Ultra‑Professional HTML Report Generator – RebarAgent
- Tekla‑level BBS table with full shape SVG rendering
- QR code encodes project info (name, listofer, date, user)
- Branded footer, signature block, A4‑optimised layout
- Automatic fallback to DB for project/client names
"""

import datetime
import os
import webbrowser
import json
import html as html_mod
import sqlite3

from config import WEIGHT_COEFFICIENT, DEFAULT_REBAR_GRADE, DB_PATH, APP_NAME
from shapes.definitions import default_shape_registry
from shapes.svg_render import generate_shape_svg
from db.models import RebarModel
from utils.report_brand import page_css, footer_html, copilot_strip_html, BRAND

import qrcode
from qrcode.image.svg import SvgPathImage

# ----------------------------------------------------------------------
# Company branding
# ----------------------------------------------------------------------
COMPANY_INFO = {
    "name": "RebarAgent",
    "phone": "+98 916 068 4552",
    "website": "https://github.com/Tahmoures54/AiRebar",
    "tagline": "Next‑Gen Rebar Detailing & BBS Automation",
    "brand_color": "#1e3a8a",
}

WHATSAPP_LINK = f"https://wa.me/{''.join(filter(str.isdigit, COMPANY_INFO['phone']))}"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _generate_qr_svg(data: str, size: int = 60) -> str:
    """Return an inline SVG QR code containing *data*."""
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=factory,
                        fill_color=COMPANY_INFO['brand_color'],
                        back_color="white")
    return img.to_string(encoding='unicode')


def _inline_stirrup_svg():
    return '''<svg width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
        <line x1="10" y1="30" x2="40" y2="30" stroke="#1e3a8a" stroke-width="4" stroke-linecap="round"/>
        <line x1="10" y1="30" x2="10" y2="10" stroke="#1e3a8a" stroke-width="4" stroke-linecap="round"/>
        <line x1="40" y1="30" x2="40" y2="10" stroke="#1e3a8a" stroke-width="4" stroke-linecap="round"/>
        <line x1="10" y1="10" x2="18" y2="10" stroke="#1e3a8a" stroke-width="3" stroke-linecap="round"/>
        <line x1="40" y1="10" x2="32" y2="10" stroke="#1e3a8a" stroke-width="3" stroke-linecap="round"/>
    </svg>'''


def _get_cutting_source(project_id, listofer_number, bar_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT source_type, source_id
            FROM cutting_assignments
            WHERE project_id = ? AND listofer_number = ? AND rebar_id = ?
            LIMIT 1
        """, (project_id, listofer_number or 0, bar_id))
        row = cur.fetchone()
        conn.close()
        if row:
            source_type, source_id = row
            return f"Stock #{source_id}" if source_type == 'stock' else f"Scrap #{source_id}"
        return "—"
    except Exception:
        return "—"


def _extract_shape_code(shape_name):
    if not shape_name:
        return ""
    s = str(shape_name).strip()
    return s.split(" - ")[0].strip() if " - " in s else s


# ----------------------------------------------------------------------
# Main HTML generation
# ----------------------------------------------------------------------
def generate_html_report(project_id, project_name, client_name="",
                         listofer_number=None):
    rebars = RebarModel.get_for_project(project_id, listofer_number=listofer_number)
    if not rebars:
        return "<html><body><h2>No reinforcement data found.</h2></body></html>"

    # ---- Fallback: fetch project / client from DB if missing ----
    if not project_name or not client_name:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.execute("SELECT name, client FROM projects WHERE id=?", (project_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                if not project_name:
                    project_name = row[0] or "Unnamed Project"
                if not client_name:
                    client_name = row[1] or ""
        except Exception:
            pass

    # Group by listofer number
    groups = {}
    for row in rebars:
        lf = row[1]
        if lf not in groups:
            groups[lf] = {"desc": row[2] or "", "items": []}
        groups[lf]["items"].append(row)

    now = datetime.datetime.now().strftime("%d %B %Y, %H:%M")

    # Extract the user who added the first rebar entry
    first_row = rebars[0]
    user_name = first_row[10] if len(first_row) >= 11 else "Unknown"
    if not user_name:
        user_name = "Unknown"

    # Build QR content – project metadata
    qr_data = (
        f"Project: {project_name}\n"
        f"Listofer: {listofer_number or 'All'}\n"
        f"Date: {now}\n"
        f"Prepared by: {user_name}"
    )
    qr_svg = _generate_qr_svg(qr_data, size=60)

    safe_project = html_mod.escape(project_name) if project_name else "Unnamed Project"
    safe_client = html_mod.escape(client_name) if client_name else "N/A"

    # ------------------------------------------------------------------
    # CSS – on‑screen A4‑like page + perfect print
    # ------------------------------------------------------------------
    css = page_css() + """
    <style>
    .listofer-section { margin-top: 28px; }
    .listofer-section h2 { color: #134e4a; font-size: 18px; border-left: 5px solid #0f766e; padding-left: 10px; margin-bottom: 8px; }
    .svg-container { width: 160px; height: 100px; display: flex; align-items: center; justify-content: center; margin: 0 auto; }
    .shape-name { font-size: 8px; color: #64748b; margin-top: 3px; }
    .source-stock { color: #166534; font-weight: bold; }
    .source-scrap { color: #b45309; font-weight: bold; }
    .source-unknown { color: #94a3b8; }
    .header-left { display: flex; align-items: center; gap: 14px; }
    </style>
    """

    # ------------------------------------------------------------------
    # HTML Body
    # ------------------------------------------------------------------
    html = f"""<html>
<head>
<meta charset="UTF-8">
<title>Bar Bending Schedule – {safe_project}</title>
{css}
</head>
<body>
<div class="page">

<div class="report-header">
    <div class="header-left">
        <div class="company-logo">{_inline_stirrup_svg()}</div>
        <div class="header-text">
            <div class="company-name">{html_mod.escape(COMPANY_INFO['name'])}</div>
            <div class="header-title">Bar Bending Schedule</div>
            <div class="header-subtitle">{html_mod.escape(COMPANY_INFO['tagline'])}</div>
        </div>
    </div>
    <div class="header-right">
        <div class="qr-code">{qr_svg}</div>
        <p>Scan for details</p>
    </div>
</div>

<div class="project-info">
    <div>
        <p><span class="label">Project:</span> {safe_project}</p>
        <p><span class="label">Client:</span> {safe_client}</p>
        <p><span class="label">Prepared by:</span> {html_mod.escape(user_name)}</p>
    </div>
    <div>
        <p><span class="label">Report Date:</span> {html_mod.escape(now)}</p>
        <p><span class="label">Contact:</span> <a href="{WHATSAPP_LINK}">WhatsApp Support</a></p>
    </div>
</div>
"""
    try:
        from logic.agent_brain import analyze_project
        from utils.i18n import get_language
        rep = analyze_project(project_id)
        html += copilot_strip_html(rep.health_score, rep.headline, get_language())
    except Exception:
        html += copilot_strip_html(None, BRAND["tagline_en"])


    # ... rest of report generation (identical to previous version, omitted for brevity) ...
    # The full function continues with the same aggregation and table code.
    # I'll include it completely to ensure it's ready to use.

    # Aggregation
    agg_by_dia = {}
    total_qty = 0
    total_weight = 0.0
    total_length_mm = 0.0

    for lf_num, group in groups.items():
        desc = html_mod.escape(group["desc"])
        safe_lf = html_mod.escape(str(lf_num))

        html += f'<div class="listofer-section">'
        html += f'<h2>Listofer: {safe_lf}</h2>'
        if desc:
            html += f'<p class="listofer-desc">{desc}</p>'

        html += """
        <table>
        <thead>
        <tr>
            <th>No</th><th>Pos</th><th>Dia</th><th>Grade</th><th>Qty</th>
            <th>Length (mm)</th><th>Unit Wt (kg)</th><th>Shape</th>
            <th>Dimensions</th><th>Location</th><th>Element</th><th>Source</th>
        </tr>
        </thead>
        <tbody>
        """

        for idx, bar in enumerate(group["items"], 1):
            # Correctly handle the new 14-column format (standard included)
            if len(bar) >= 14:
                rid, lf, desc_, pos, dia, shape_name, dims_json, qty, location, etype, user, date, grade, standard = bar
            elif len(bar) >= 13:
                rid, lf, desc_, pos, dia, shape_name, dims_json, qty, location, etype, user, date, grade = bar
                standard = ""
            else:
                rid, lf, desc_, pos, dia, shape_name, dims_json, qty, location, etype, user, date = bar
                grade = DEFAULT_REBAR_GRADE
                standard = ""

            try:
                dims = json.loads(dims_json) if dims_json else {}
            except Exception:
                dims = {}
            dims_str = ", ".join(f"{k}={v:.0f}" for k, v in dims.items())

            try:
                length_mm = default_shape_registry.calc_shape_length(shape_name, dims, dia)
            except Exception:
                length_mm = 0.0
            length_m = length_mm / 1000.0
            weight_per_piece = length_m * (dia ** 2) * WEIGHT_COEFFICIENT
            row_weight = weight_per_piece * qty

            key = (dia, grade)
            agg_by_dia.setdefault(key, {"qty": 0, "weight": 0.0, "length": 0.0})
            agg_by_dia[key]["qty"] += qty
            agg_by_dia[key]["weight"] += row_weight
            agg_by_dia[key]["length"] += length_mm * qty

            shape_code = _extract_shape_code(shape_name)
            try:
                dims_json_str = json.dumps(dims)
                svg_code = generate_shape_svg(shape_code, dims_json_str, dia, width=160, height=100)
            except Exception:
                svg_code = "N/A"

            source_str = _get_cutting_source(project_id, lf_num, rid)
            if "Stock" in source_str:
                source_class = "source-stock"
            elif "Scrap" in source_str:
                source_class = "source-scrap"
            else:
                source_class = "source-unknown"

            html += f"""
            <tr>
                <td>{idx}</td>
                <td>{html_mod.escape(str(pos))}</td>
                <td>Ø{dia}</td>
                <td>{html_mod.escape(str(grade))}</td>
                <td>{qty}</td>
                <td>{length_mm:.1f}</td>
                <td>{weight_per_piece:.2f}</td>
                <td>
                    <div class="svg-container">{svg_code}</div>
                    <div class="shape-name">{html_mod.escape(shape_name)}</div>
                </td>
                <td>{html_mod.escape(dims_str)}</td>
                <td>{html_mod.escape(str(location or "-"))}</td>
                <td>{html_mod.escape(str(etype or "-"))}</td>
                <td class="{source_class}">{html_mod.escape(source_str)}</td>
            </tr>
            """

            total_qty += qty
            total_weight += row_weight
            total_length_mm += length_mm * qty

        html += "</tbody></table></div>"

    total_length_m = total_length_mm / 1000.0
    html += f"""
    <div class="summary-grid">
        <div class="summary-card">
            <div class="label">Total Pieces</div>
            <div class="value">{total_qty}</div>
        </div>
        <div class="summary-card">
            <div class="label">Total Length (m)</div>
            <div class="value">{total_length_m:.1f}</div>
        </div>
        <div class="summary-card">
            <div class="label">Total Weight (kg)</div>
            <div class="value">{total_weight:.2f}</div>
        </div>
    </div>

    <div class="listofer-section">
        <h2>Summary by Diameter &amp; Grade</h2>
        <table class="breakdown-table">
        <tr><th>Diameter</th><th>Grade</th><th>Quantity</th><th>Length (m)</th><th>Weight (kg)</th></tr>
    """
    for (d, g) in sorted(agg_by_dia.keys()):
        data = agg_by_dia[(d, g)]
        html += f"""
        <tr>
            <td>Ø{d}</td>
            <td>{html_mod.escape(str(g))}</td>
            <td>{data['qty']}</td>
            <td>{data['length']/1000:.2f}</td>
            <td>{data['weight']:.2f}</td>
        </tr>"""
    html += '</table></div>'

    html += """
    <div class="signatures">
        <div class="signature-box">
            <div class="signature-line"></div>
            <div class="signature-label">Site Supervisor</div>
        </div>
        <div class="signature-box">
            <div class="signature-line"></div>
            <div class="signature-label">Inspecting Engineer</div>
        </div>
    </div>
    """

    try:
        from utils.i18n import get_language
        lang = get_language()
    except Exception:
        lang = "en"
    html += footer_html(lang)
    html += """
</div><!-- end .page -->
</body></html>
    """

    return html


def export_html(project_id, project_name, client_name,
                output_path, listofer_number=None):
    content = generate_html_report(
        project_id, project_name, client_name,
        listofer_number=listofer_number
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    webbrowser.open("file:///" + os.path.abspath(output_path).replace("\\", "/"))