# config.py
# Global configuration constants for the RebarAgent application.

import os
import json

from utils.envfile import load_project_env

load_project_env()

APP_NAME = "RebarAgent"
APP_VERSION = "1.7.0"

from enum import Enum

class RebarGrade(str, Enum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    S240 = "S240"
    S400 = "S400"
    B500B = "B500B"

class AppTheme(str, Enum):
    TURQUOISE = "turquoise"
    LIGHT = "light"
    DARK = "dark"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, "rebar_database.db")
DB_PATH = DATABASE_FILE
APP_CONFIG_FILE = os.path.join(BASE_DIR, "app_config.json")
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")

HIDDEN_LICENSE_DIR = (
    os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "RebarAgent")
    if os.name == "nt" else
    os.path.join(os.path.expanduser("~"), ".config", "rebaragent")
)
HIDDEN_LICENSE_FILE = os.path.join(HIDDEN_LICENSE_DIR, "license.dat")

BACKUP_SUFFIX = ".backup"
AUTO_SAVE_INTERVAL_MS = 60_000

TRIAL_PERIOD_DAYS = 14
MAX_TRIAL_RECORDS = 80
MAX_TRIAL_PROJECTS = 2


def _env_str(key: str, default: str = "") -> str:
    val = os.environ.get(key, "")
    return val.strip() if isinstance(val, str) and val.strip() else default


def _env_int(key: str, default: int) -> int:
    raw = _env_str(key, "")
    if not raw:
        return default
    try:
        return int(float(raw.replace(",", "").replace("_", "")))
    except ValueError:
        return default


REVENUE_PLANS = {
    "trial": {
        "code": "trial", "name_en": "Trial", "name_fa": "آزمایشی", "days": 14,
        "price_irr": 0, "price_usd": 0, "max_records": 80, "max_projects": 2,
        "features": {"export_excel": True, "export_pdf": True, "export_html": True, "export_bvbs": False,
            "cutting_plan": True, "agent_insights": True, "scrap_bank": True, "stock_manager": True,
            "custom_shapes": False, "priority_support": False},
    },
    "pro": {
        "code": "pro", "name_en": "Pro", "name_fa": "حرفه‌ای",
        "durations": {
            "pro_3m": {"days": 90, "price_irr": _env_int("REBARAGENT_PRICE_PRO_3M_IRR", 2_900_000),
                       "price_usd": _env_int("REBARAGENT_PRICE_PRO_3M_USD", 49)},
            "pro_6m": {"days": 180, "price_irr": _env_int("REBARAGENT_PRICE_PRO_6M_IRR", 4_900_000),
                       "price_usd": _env_int("REBARAGENT_PRICE_PRO_6M_USD", 79)},
            "pro_1y": {"days": 365, "price_irr": _env_int("REBARAGENT_PRICE_PRO_1Y_IRR", 7_900_000),
                       "price_usd": _env_int("REBARAGENT_PRICE_PRO_1Y_USD", 129)},
        },
        "max_records": None, "max_projects": None,
        "features": {"export_excel": True, "export_pdf": True, "export_html": True, "export_bvbs": True,
            "cutting_plan": True, "agent_insights": True, "scrap_bank": True, "stock_manager": True,
            "custom_shapes": True, "priority_support": True},
    },
    "office": {
        "code": "office", "name_en": "Office", "name_fa": "دفتری",
        "durations": {"office_1y": {"days": 365, "price_irr": _env_int("REBARAGENT_PRICE_OFFICE_1Y_IRR", 14_900_000),
                                    "price_usd": _env_int("REBARAGENT_PRICE_OFFICE_1Y_USD", 249)}},
        "max_records": None, "max_projects": None, "seats": 3,
        "features": {"export_excel": True, "export_pdf": True, "export_html": True, "export_bvbs": True,
            "cutting_plan": True, "agent_insights": True, "scrap_bank": True, "stock_manager": True,
            "custom_shapes": True, "priority_support": True},
    },
    "unlimited": {
        "code": "unlimited", "name_en": "Lifetime", "name_fa": "مادام‌العمر",
        "durations": {"unlimited": {"days": None, "price_irr": _env_int("REBARAGENT_PRICE_UNLIMITED_IRR", 24_900_000),
                                    "price_usd": _env_int("REBARAGENT_PRICE_UNLIMITED_USD", 399)}},
        "max_records": None, "max_projects": None,
        "features": {"export_excel": True, "export_pdf": True, "export_html": True, "export_bvbs": True,
            "cutting_plan": True, "agent_insights": True, "scrap_bank": True, "stock_manager": True,
            "custom_shapes": True, "priority_support": True},
    },
}

LICENSE_TYPE_ALIASES = {
    "trial": "trial", "3month": "pro", "6month": "pro", "1year": "pro",
    "pro_3m": "pro", "pro_6m": "pro", "pro_1y": "pro", "office_1y": "office", "unlimited": "unlimited",
}

PURCHASE_CONTACT = {
    "whatsapp": _env_str("REBARAGENT_WHATSAPP", "+989160684552"),
    "whatsapp_digits": "".join(ch for ch in _env_str("REBARAGENT_WHATSAPP", "+989160684552") if ch.isdigit()),
    "telegram": _env_str("REBARAGENT_TELEGRAM", "@RebarAgent"),
    "worker_url": _env_str("REBARAGENT_WORKER_URL", ""),
    "website": _env_str("REBARAGENT_WEBSITE", "https://github.com/Tahmoures54/RebarAgent"),
    "email": "license@rebaragent.local",
    "note_en": "Pay USDT (TRC20) in License Management — the app activates itself. WhatsApp is only for problems.",
    "note_fa": "در مدیریت لایسنس تتر (TRC20) بپردازید؛ برنامه خودش فعال می‌شود. واتساپ فقط برای مشکل است.",
}

# Self-serve USDT checkout (TRC20). Set REBARAGENT_USDT_TRC20 in .env
USDT_TRC20_ADDRESS = _env_str("REBARAGENT_USDT_TRC20", "")
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
USDT_PAYMENT_NETWORK = "TRC20"
USDT_PAYMENT_MAX_AGE_SEC = 7 * 24 * 3600
TRONGRID_API_URL = "https://api.trongrid.io"

STANDARD_STOCK_LENGTHS_M = [6, 12]
STANDARD_BRANCH_LENGTHS = STANDARD_STOCK_LENGTHS_M
MM_TO_M_FACTOR = 1000.0
WEIGHT_COEFFICIENT = 0.006165
STANDARD_DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40]
REBAR_GRADES = [g.value for g in RebarGrade]
DEFAULT_REBAR_GRADE = RebarGrade.A3.value
ELEMENT_TYPES = ["Foundation", "Footing", "Column", "Beam", "Slab", "Wall", "Stairs", "Stirrup", "Tie", "Link", "Other"]
MAX_STOCK_LENGTH_MM = 18_000
LOW_STOCK_THRESHOLD = 5
QUICK_ADD_DEFAULTS = {"diameter": 12, "length": 6000, "quantity": 10, "shape_code": "00", "grade": DEFAULT_REBAR_GRADE}
QUICK_ADD_SHAPE_CODES = ["00", "11", "12", "13", "21", "22", "23", "31", "32", "33"]
SUPPORTED_SHAPE_CODES = QUICK_ADD_SHAPE_CODES
SPLASH_DURATION_MS = 2500

THEMES = {
    AppTheme.TURQUOISE.value: {"bg": "#E0F7FA", "fg": "#006064", "tree_bg": "#FFFFFF", "tree_fg": "#006064", "entry_bg": "#FFFFFF", "button_bg": "#B2EBF2", "button_fg": "#004D40", "label_frame_bg": "#E0F7FA", "canvas_line": "#006064", "accent": "#00BCD4", "highlight": "#0097A7", "menu_bg": "#00BCD4", "menu_fg": "#FFFFFF"},
    AppTheme.LIGHT.value: {"bg": "#F8FAFC", "fg": "#1E293B", "tree_bg": "#FFFFFF", "tree_fg": "#1E293B", "entry_bg": "#FFFFFF", "button_bg": "#E2E8F0", "button_fg": "#0F172A", "label_frame_bg": "#F1F5F9", "canvas_line": "#334155", "accent": "#3B82F6", "highlight": "#2563EB", "menu_bg": "#3B82F6", "menu_fg": "#FFFFFF"},
    AppTheme.DARK.value: {"bg": "#0F172A", "fg": "#E2E8F0", "tree_bg": "#1E293B", "tree_fg": "#F1F5F9", "entry_bg": "#1E293B", "button_bg": "#334155", "button_fg": "#F8FAFC", "label_frame_bg": "#1E293B", "canvas_line": "#94A3B8", "accent": "#38BDF8", "highlight": "#0EA5E9", "menu_bg": "#0EA5E9", "menu_fg": "#0F172A"},
}
DEFAULT_THEME = AppTheme.TURQUOISE.value
LOG_LEVEL = "INFO"
EXPORT_DATE_FORMAT = "%Y-%m-%d"
EXPORT_FILE_PREFIX = "BBS_Report"
COMPANY_INFO = {"name": "Sample Construction Co.", "logo": "", "engineer": "Engineering Department", "website": "www.sample-construction.com", "phone": "+1 (555) 123-4567"}
FILTER_SHOW_ALL = "-- Show All --"
FILTER_SHOW_ALL_SENTINELS = frozenset({
    "-- Show All --",
    "-- نمایش همه --",
    "-- All --",
})
VERSION = APP_VERSION


def is_all_listofer_filter(value) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    if text in FILTER_SHOW_ALL_SENTINELS:
        return True
    return text == FILTER_SHOW_ALL

MENU_LABELS = {
    "file": "File", "new_project": "New Project...", "open_project": "Open Project...", "project_manager": "Project Manager...",
    "export_excel": "Export Excel...", "export_pdf": "Export PDF...", "print_listofer": "📋 Print Listofer...",
    "export_bvbs": "🗂️ Export BVBS (BIM)...", "import_bvbs": "📥 Import BVBS (BIM)...", "settings": "Settings...", "exit": "Exit",
    "tools": "Tools", "lap_splice": "🔧 Lap Splice Calculator...", "cutting_plan_all": "🧠 Cutting Plan (All)",
    "cutting_plan_selected": "🧠 Cutting Plan (Selected)", "scrap_manager": "🧩 Smart Scrap Bank...",
    "stock_manager": "🧱 Stock Manager...", "custom_shape_designer": "✏️ Custom Shape Designer...", "help": "Help",
    "welcome": "📖 Welcome...", "user_guide": "📖 User Guide", "about": "About",
    "license_management": "🔑 License Management...", "contact_developer": "Contact Developer",
}

TOOLBAR_BUTTONS = {
    "new_rebar": "➕ New Rebar", "edit": "✏️ Edit", "delete": "🗑️ Delete", "print_listofer": "📋 Print Listofer",
    "cutting_plan": "🧠 Cutting Plan", "agent_insights": "🤖 Insights", "lap_splice": "🔧 Lap Splice Calc",
    "scrap_manager": "🧩 Smart Scrap Bank", "stock_manager": "🧱 Stock", "projects": "📁 Projects",
}

ERROR_MSGS = {
    "no_project": "No active project. Create a new one?",
    "wrong_password": "Incorrect. {attempts} attempt(s) left.",
    "access_denied": "The application will close.",
    "delete_confirm": "Delete selected rebar(s)?",
    "no_selection": "No row selected.",
}

FONT_DEFAULTS = {"tagline": ("Arial", 11, "italic"), "status": ("Arial", 10, "italic"), "summary": ("Arial", 10), "db_path": ("Arial", 9)}

def should_show_welcome():
    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return True
    return not cfg.get("hide_welcome", False)

def get_default_project_info():
    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("project_info", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_recent_projects(limit=8):
    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        items = cfg.get("recent_projects") or []
        return items[:limit]
    except Exception:
        return []

def add_recent_project(project_id, name, client=""):
    try:
        try:
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
        items = [x for x in (cfg.get("recent_projects") or []) if x.get("id") != project_id]
        items.insert(0, {"id": project_id, "name": name or f"Project {project_id}", "client": client or ""})
        cfg["recent_projects"] = items[:12]
        with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
