# utils/excel_import.py
"""Import rebars from a simple Excel template into a project."""

from __future__ import annotations

import json
import datetime
import re
from typing import Any, Dict, List

import pandas as pd

from db.models import ListoferModel, RebarModel
from config import DEFAULT_REBAR_GRADE
from utils.logger import setup_logger

logger = setup_logger("RebarAgent.ExcelImport")

COL_MAP = {
    "listofer": [
        "listofer", "listofer_no", "lf", "lf_no", "sheet", "bbs",
        "لیستوفر", "شماره_لیستوفر", "شمارهلیستوفر",
    ],
    "pos": [
        "pos", "mark", "bar_mark", "ref", "position",
        "پوز", "شماره_پوز", "علامت", "شمارهپوز",
    ],
    "diameter": [
        "diameter", "dia", "d", "ø", "phi", "bar_dia", "size",
        "قطر", "قطرمیلگرد", "فی", "سایز",
    ],
    "shape": [
        "shape", "shape_code", "shape_name", "code",
        "شکل", "کد_شکل", "کدشکل", "کد",
    ],
    "quantity": [
        "quantity", "qty", "count", "n", "nos",
        "تعداد", "تعدادشاخه", "عدد",
    ],
    "a": ["a", "dim_a", "length", "l", "cut_length", "طول", "طول_برش", "طولبرش"],
    "b": ["b", "dim_b", "بعد_ب"],
    "c": ["c", "dim_c", "بعد_ج"],
    "d": ["d", "dim_d"],
    "e": ["e", "dim_e"],
    "grade": ["grade", "steel_grade", "رده", "نوع_فولاد", "رده_فولاد"],
    "location": ["location", "loc", "zone", "محل", "زون", "ناحیه"],
    "element": ["element", "element_type", "member", "عضو", "المان", "نوع_عضو"],
    "standard": ["standard", "std", "استاندارد"],
    "description": ["description", "listofer_desc", "desc", "شرح", "توضیحات"],
}

_STANDARD_NORM = {
    "bs": "bs", "bs8666": "bs", "uk": "bs",
    "ir": "ir", "iran": "ir", "mabhas": "ir", "mabhas9": "ir", "m9": "ir",
    "aci": "aci", "aci318": "aci",
    "ec": "ec", "ec2": "ec", "eurocode": "ec", "eurocode2": "ec",
    "is": "is", "is2502": "is",
    "gb": "gb", "jis": "jis", "as": "as", "nbr": "nbr",
    "مبحث9": "ir", "مبحث_9": "ir", "مبحث۹": "ir",
}


def _norm(s) -> str:
    if s is None:
        return ""
    text = str(s).strip().lower().replace(" ", "_")
    text = text.replace("\u200c", "")  # ZWNJ
    return text


def _is_blank(val) -> bool:
    if val is None:
        return True
    try:
        if pd.isna(val):
            return True
    except Exception:
        pass
    text = str(val).strip()
    return (not text) or text.lower() in {"nan", "none", "-"}


def _map_columns(columns) -> Dict[str, str]:
    mapping = {}
    norms = {_norm(c): c for c in columns}
    for canon, aliases in COL_MAP.items():
        for a in aliases:
            if a in norms:
                mapping[canon] = norms[a]
                break
    return mapping


def normalize_standard(value: str) -> str:
    key = _norm(value).replace("_", "")
    return _STANDARD_NORM.get(key, key or "bs")


def normalize_shape_code(value: str) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return "00"
    match = re.match(r"^(\d{2})", text)
    if match:
        return match.group(1)
    return text


def _shape_dimensions(shape: str, dims: Dict[str, float]) -> Dict[str, float]:
    """Straight BS/IR bars use L; Excel templates often put cut length in A."""
    code = normalize_shape_code(shape)
    if code in {"00", "01"} and "L" not in dims and "A" in dims:
        dims = dict(dims)
        dims["L"] = dims["A"]
    return dims


def read_import_preview(path: str, max_rows: int = 20) -> Dict[str, Any]:
    df = pd.read_excel(path, engine="openpyxl")
    df = df.dropna(how="all")
    colmap = _map_columns(df.columns)
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "mapped": colmap,
        "preview": df.head(max_rows).fillna("").astype(str).values.tolist(),
        "missing_required": [k for k in ("diameter", "quantity") if k not in colmap],
    }


def import_rebars_from_excel(
    path: str,
    project_id: int,
    default_listofer: str = "IMP-01",
    user: str = "excel_import",
    dry_run: bool = False,
) -> Dict[str, Any]:
    df = pd.read_excel(path, engine="openpyxl")
    df = df.dropna(how="all")
    colmap = _map_columns(df.columns)
    if "diameter" not in colmap or "quantity" not in colmap:
        raise ValueError(
            "Excel must have columns for Diameter and Quantity "
            f"(found: {list(df.columns)})"
        )

    today = datetime.datetime.now().isoformat()[:10]
    imported = 0
    skipped = 0
    errors: List[str] = []
    listofer_cache: Dict[str, int] = {}

    for idx, row in df.iterrows():
        try:
            if _is_blank(row[colmap["diameter"]]) and _is_blank(row[colmap["quantity"]]):
                skipped += 1
                continue
            dia = float(row[colmap["diameter"]])
            qty = int(float(row[colmap["quantity"]]))
            if dia <= 0 or qty <= 0:
                skipped += 1
                continue

            lf_num = str(row[colmap["listofer"]]).strip() if "listofer" in colmap else default_listofer
            if _is_blank(lf_num):
                lf_num = default_listofer
            lf_desc = ""
            if "description" in colmap:
                lf_desc = "" if _is_blank(row[colmap["description"]]) else str(row[colmap["description"]]).strip()

            if not dry_run and lf_num not in listofer_cache:
                listofer_cache[lf_num] = ListoferModel.get_or_create(project_id, lf_num, lf_desc)
            elif dry_run:
                listofer_cache.setdefault(lf_num, 0)
            lid = listofer_cache[lf_num]

            pos = str(row[colmap["pos"]]).strip() if "pos" in colmap else f"R{idx+1}"
            if _is_blank(pos):
                pos = f"R{idx+1}"

            shape = normalize_shape_code(row[colmap["shape"]]) if "shape" in colmap else "00"

            dims: Dict[str, float] = {}
            for key in ("a", "b", "c", "d", "e"):
                if key in colmap:
                    try:
                        if _is_blank(row[colmap[key]]):
                            continue
                        val = float(row[colmap[key]])
                        if val > 0:
                            dims[key.upper()] = val
                    except Exception:
                        pass
            dims = _shape_dimensions(shape, dims)

            grade = DEFAULT_REBAR_GRADE
            if "grade" in colmap and not _is_blank(row[colmap["grade"]]):
                grade = str(row[colmap["grade"]]).strip()

            location = ""
            if "location" in colmap and not _is_blank(row[colmap["location"]]):
                location = str(row[colmap["location"]]).strip()

            element = ""
            if "element" in colmap and not _is_blank(row[colmap["element"]]):
                element = str(row[colmap["element"]]).strip()

            standard = "bs"
            if "standard" in colmap and not _is_blank(row[colmap["standard"]]):
                standard = normalize_standard(str(row[colmap["standard"]]).strip())

            if not dry_run:
                RebarModel.add(
                    lid, pos, dia, shape, json.dumps(dims), qty,
                    location, element, user, today,
                    grade=grade, standard=standard,
                )
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Row {idx}: {e}")
            if len(errors) > 15:
                break

    return {
        "imported": imported,
        "skipped": skipped,
        "listofers": len(listofer_cache),
        "errors": errors,
        "dry_run": dry_run,
    }


def create_import_template(path: str) -> str:
    df = pd.DataFrame(
        [
            {
                "Listofer": "F-01",
                "Description": "Foundation",
                "Pos": "B1",
                "Diameter": 16,
                "Shape": "00",
                "A": 5200,
                "B": "",
                "C": "",
                "Quantity": 24,
                "Grade": DEFAULT_REBAR_GRADE,
                "Location": "Foundation",
                "Element": "Footing",
                "Standard": "bs",
            },
            {
                "Listofer": "F-01",
                "Description": "Foundation",
                "Pos": "S1",
                "Diameter": 10,
                "Shape": "21",
                "A": 400,
                "B": 300,
                "C": "",
                "Quantity": 40,
                "Grade": DEFAULT_REBAR_GRADE,
                "Location": "Foundation",
                "Element": "Stirrup",
                "Standard": "bs",
            },
        ]
    )
    df.to_excel(path, index=False, engine="openpyxl")
    return path
