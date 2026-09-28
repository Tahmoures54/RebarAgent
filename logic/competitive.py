# logic/competitive.py
"""Site-office tools that Excel and generic cutters usually skip."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple

from db.models import RebarModel
from shapes.definitions import default_shape_registry
from logic.stock_intelligence import analyze_stock_intelligence, format_stock_intelligence_report


def first_fit_decreasing(pieces_m: Sequence[float], stock_m: float, kerf_m: float = 0.0) -> Dict[str, Any]:
    """Pack pieces onto identical stock bars. Pieces longer than stock are unfit."""
    stock_m = float(stock_m)
    kerf_m = max(0.0, float(kerf_m))
    fit: List[float] = []
    unfit: List[float] = []
    for p in pieces_m:
        p = float(p)
        if p <= 0:
            continue
        if p > stock_m + 1e-9:
            unfit.append(p)
        else:
            fit.append(p)
    fit.sort(reverse=True)
    bins: List[float] = []
    for p in fit:
        placed = False
        for i, rem in enumerate(bins):
            extra = kerf_m if rem < stock_m - 1e-12 else 0.0
            if p + extra <= rem + 1e-9:
                bins[i] = rem - p - extra
                placed = True
                break
        if not placed:
            bins.append(stock_m - p)
    bars = len(bins)
    used = sum(fit)
    purchased = bars * stock_m
    waste = max(0.0, purchased - used)
    util = (used / purchased * 100.0) if purchased else 0.0
    return {
        "stock_m": stock_m,
        "bars": bars,
        "used_m": used,
        "purchased_m": purchased,
        "waste_m": waste,
        "utilization_pct": util,
        "unfit": unfit,
        "piece_count": len(fit),
    }


def collect_project_pieces(project_id: int) -> List[Tuple[float, str, float]]:
    import json
    from config import DEFAULT_REBAR_GRADE

    out: List[Tuple[float, str, float]] = []
    for row in RebarModel.get_for_project(project_id) or []:
        try:
            dia = float(row[4])
            shape = (row[5] or "00").strip()
            dims_raw = row[6]
            qty = int(row[7] or 0)
            grade = str(row[12] if len(row) > 12 else DEFAULT_REBAR_GRADE) or DEFAULT_REBAR_GRADE
            if isinstance(dims_raw, str):
                try:
                    dims = json.loads(dims_raw) if dims_raw else {}
                except Exception:
                    dims = {}
            elif isinstance(dims_raw, dict):
                dims = dims_raw
            else:
                dims = {}
            unit_mm = float(default_shape_registry.calc_shape_length(shape, dims, dia) or 0)
            if unit_mm <= 0 or qty <= 0:
                continue
            unit_m = unit_mm / 1000.0
            for _ in range(qty):
                out.append((dia, grade, unit_m))
        except Exception:
            continue
    return out


def compare_stock_strategies(project_id: int, kerf_m: float = 0.0) -> Dict[str, Any]:
    pieces = collect_project_pieces(project_id)
    by_group: Dict[Tuple[float, str], List[float]] = defaultdict(list)
    for dia, grade, length_m in pieces:
        by_group[(dia, grade)].append(length_m)

    def pack_all(stock_m: float) -> Dict[str, Any]:
        total = {"bars": 0, "used_m": 0.0, "purchased_m": 0.0, "waste_m": 0.0, "unfit": 0, "groups": []}
        for (dia, grade), lens in sorted(by_group.items()):
            r = first_fit_decreasing(lens, stock_m, kerf_m)
            total["bars"] += r["bars"]
            total["used_m"] += r["used_m"]
            total["purchased_m"] += r["purchased_m"]
            total["waste_m"] += r["waste_m"]
            total["unfit"] += len(r["unfit"])
            total["groups"].append({"diameter": dia, "grade": grade, "bars": r["bars"], "waste_m": r["waste_m"], "utilization_pct": r["utilization_pct"]})
        total["utilization_pct"] = (
            total["used_m"] / total["purchased_m"] * 100.0 if total["purchased_m"] else 0.0
        )
        return total

    only12 = pack_all(12.0)
    only6 = pack_all(6.0)

    mixed = {"bars_6": 0, "bars_12": 0, "used_m": 0.0, "purchased_m": 0.0, "waste_m": 0.0, "unfit": 0}
    for lens in by_group.values():
        short = [p for p in lens if p <= 6.0 + 1e-9]
        longp = [p for p in lens if p > 6.0 + 1e-9]
        a = first_fit_decreasing(short, 6.0, kerf_m)
        b = first_fit_decreasing(longp, 12.0, kerf_m)
        mixed["bars_6"] += a["bars"]
        mixed["bars_12"] += b["bars"]
        mixed["used_m"] += a["used_m"] + b["used_m"]
        mixed["purchased_m"] += a["purchased_m"] + b["purchased_m"]
        mixed["waste_m"] += a["waste_m"] + b["waste_m"]
        mixed["unfit"] += len(a["unfit"]) + len(b["unfit"])
    mixed["bars"] = mixed["bars_6"] + mixed["bars_12"]
    mixed["utilization_pct"] = (
        mixed["used_m"] / mixed["purchased_m"] * 100.0 if mixed["purchased_m"] else 0.0
    )

    winner = "12 m only"
    best_waste = only12["waste_m"]
    if only6["unfit"] == 0 and only6["waste_m"] + 1e-6 < best_waste:
        winner = "6 m only"
        best_waste = only6["waste_m"]
    if mixed["waste_m"] + 1e-6 < best_waste:
        winner = "mixed 6 m + 12 m"

    return {
        "piece_count": len(pieces),
        "groups": len(by_group),
        "only_12": only12,
        "only_6": only6,
        "mixed": mixed,
        "winner": winner,
    }


def format_compare_report(cmp: Dict[str, Any]) -> str:
    a, b, m = cmp["only_12"], cmp["only_6"], cmp["mixed"]
    lines = [
        f"Pieces: {cmp['piece_count']}  ·  diameter/grade groups: {cmp['groups']}",
        f"Recommended stock mix: {cmp['winner']}",
        "",
        f"12 m only:  {a['bars']} bars  ·  waste {a['waste_m']:.2f} m  ·  {a['utilization_pct']:.1f}%  ·  unfit {a['unfit']}",
        f"6 m only:   {b['bars']} bars  ·  waste {b['waste_m']:.2f} m  ·  {b['utilization_pct']:.1f}%  ·  unfit {b['unfit']}",
        f"Mixed:      {m['bars_6']}×6 m + {m['bars_12']}×12 m  ·  waste {m['waste_m']:.2f} m  ·  {m['utilization_pct']:.1f}%",
        "",
        "This is a fast first-fit estimate. Confirm with Cutting Plan before buying.",
    ]
    return "\n".join(lines)


def find_duplicate_marks(project_id: int) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[Any, Any], List[Any]] = defaultdict(list)
    for row in RebarModel.get_for_project(project_id) or []:
        lf = row[1]
        pos = str(row[3] or "").strip()
        if not pos:
            continue
        groups[(lf, pos)].append(row)
    dups = []
    for (lf, pos), rows in sorted(groups.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
        if len(rows) < 2:
            continue
        dups.append({
            "listofer": lf,
            "mark": pos,
            "count": len(rows),
            "diameters": sorted({float(r[4]) for r in rows}),
            "qtys": [int(r[7] or 0) for r in rows],
        })
    return dups


def format_duplicate_report(dups: List[Dict[str, Any]]) -> str:
    if not dups:
        return "No duplicate marks in this project."
    lines = [f"{len(dups)} duplicate mark(s):", ""]
    for d in dups:
        lines.append(
            f"Listofer {d['listofer']}  mark {d['mark']}  ×{d['count']}  "
            f"Ø{', '.join(f'{x:g}' for x in d['diameters'])}  qty {d['qtys']}"
        )
    return "\n".join(lines)


def buy_list(project_id: int, preferred_bar_m: float = 12.0) -> Dict[str, Any]:
    return analyze_stock_intelligence(project_id, preferred_bar_mm=preferred_bar_m * 1000.0)


def format_buy_list(project_id: int, preferred_bar_m: float = 12.0) -> str:
    return format_stock_intelligence_report(buy_list(project_id, preferred_bar_m))
