# logic/site_reports.py
"""Extra site-office reports used by Site tools."""
from __future__ import annotations

from logic.competitive import collect_project_pieces


def long_bar_report(project_id: int, stock_m: float = 12.0) -> str:
    from logic.calculator import calculate_weight

    over = []
    mid = []
    for dia, grade, length_m in collect_project_pieces(project_id):
        rec = (dia, grade, length_m)
        if length_m > stock_m + 1e-9:
            over.append(rec)
        elif length_m > 6.0 + 1e-9:
            mid.append(rec)
    lines = [
        f"Stock reference: {stock_m:g} m",
        f"Pieces longer than {stock_m:g} m (need splice / special order): {len(over)}",
        f"Pieces between 6 m and {stock_m:g} m (12 m stock only): {len(mid)}",
        "",
    ]
    if over:
        lines.append("Over-length:")
        for dia, grade, L in sorted(over, key=lambda x: -x[2])[:40]:
            wt = 0.0
            try:
                _, piece = calculate_weight(dia, L * 1000.0)
                wt = piece
            except Exception:
                pass
            lines.append(f"  Ø{dia:g} {grade}  {L:.3f} m  ({wt:.2f} kg)")
        if len(over) > 40:
            lines.append(f"  … {len(over) - 40} more")
        lines.append("")
    if not over and not mid:
        lines.append("All pieces fit a 6 m bar.")
    elif not over:
        lines.append("No splice required if 12 m stock is available.")
    return "\n".join(lines)


def scrap_match_report(project_id: int) -> str:
    from db.models import ScrapModel
    from config import DEFAULT_REBAR_GRADE
    from collections import defaultdict

    scraps_by = defaultdict(list)
    try:
        rows = ScrapModel.get_all_scraps(project_id) or []
    except Exception:
        rows = []
    for row in rows:
        try:
            used = 0
            if len(row) > 7:
                used = int(row[7] or 0)
            if used:
                continue
            dia = float(row[2])
            length_m = float(row[3]) / 1000.0
            grade = str(row[4] if len(row) > 4 and row[4] else DEFAULT_REBAR_GRADE)
            sid = row[0]
            scraps_by[(dia, grade)].append({"id": sid, "m": length_m})
        except Exception:
            continue

    pieces_by = defaultdict(list)
    for dia, grade, length_m in collect_project_pieces(project_id):
        pieces_by[(dia, grade)].append(length_m)

    keys = sorted(set(scraps_by) | set(pieces_by))
    if not keys:
        return "No scraps or BBS pieces to match."

    lines = ["Greedy scrap → piece match (does not consume inventory):", ""]
    total_hits = 0
    leftover_scraps = 0
    unmatched_pieces = 0
    for key in keys:
        dia, grade = key
        scraps = sorted(scraps_by.get(key, []), key=lambda s: -s["m"])
        pieces = sorted(pieces_by.get(key, []), reverse=True)
        hits = []
        used_idx = set()
        for s in scraps:
            found = None
            for i, p in enumerate(pieces):
                if i in used_idx:
                    continue
                if p <= s["m"] + 1e-9:
                    found = i
                    break
            if found is None:
                leftover_scraps += 1
                continue
            used_idx.add(found)
            hits.append((s, pieces[found]))
            total_hits += 1
        unmatched = len(pieces) - len(used_idx)
        unmatched_pieces += unmatched
        lines.append(
            f"Ø{dia:g} {grade}: {len(scraps)} scrap(s), {len(pieces)} piece(s), "
            f"{len(hits)} match(es), {unmatched} piece(s) still need stock"
        )
        for s, p in hits[:8]:
            lines.append(f"  scrap #{s['id']} {s['m']:.3f} m  →  piece {p:.3f} m")
        if len(hits) > 8:
            lines.append(f"  … {len(hits) - 8} more matches")
    lines += [
        "",
        f"Matches: {total_hits}  ·  scraps unused by this greedy pass: {leftover_scraps}  ·  pieces still on stock: {unmatched_pieces}",
        "Run Cutting Plan + Confirm to apply this for real.",
    ]
    return "\n".join(lines)


def weight_roll_report(project_id: int) -> str:
    from collections import defaultdict
    from logic.calculator import calculate_weight

    acc = defaultdict(lambda: {"m": 0.0, "n": 0, "kg": 0.0})
    for dia, grade, length_m in collect_project_pieces(project_id):
        key = (dia, grade)
        acc[key]["m"] += length_m
        acc[key]["n"] += 1
        try:
            _, piece = calculate_weight(dia, length_m * 1000.0)
            acc[key]["kg"] += piece
        except Exception:
            pass
    if not acc:
        return "No positions — add bars first."
    lines = ["Weight by diameter / grade:", ""]
    total_kg = total_m = total_n = 0
    for (dia, grade), v in sorted(acc.items()):
        total_kg += v["kg"]
        total_m += v["m"]
        total_n += v["n"]
        lines.append(f"  Ø{dia:g} {grade}:  {v['n']} pcs  ·  {v['m']:.2f} m  ·  {v['kg']:.1f} kg")
    lines += ["", f"Total: {total_n} pcs  ·  {total_m:.2f} m  ·  {total_kg:.1f} kg"]
    return "\n".join(lines)


def audit_report(project_id: int) -> str:
    from db.models import RebarModel
    from logic.validation import validate_project_positions

    rows = RebarModel.get_for_project(project_id) or []
    issues = validate_project_positions(rows)
    errors = [i for i in issues if i.level == "error"]
    warns = [i for i in issues if i.level == "warning"]
    lines = [
        f"Positions: {len(rows)}",
        f"Errors: {len(errors)}  ·  Warnings: {len(warns)}",
        "",
    ]
    if not issues:
        lines.append("No issues found.")
        return "\n".join(lines)
    for i in (errors + warns)[:60]:
        pos = (i.context or {}).get("pos", "")
        lines.append(f"[{i.level}] {i.code}  mark {pos}: {i.message}")
    if len(issues) > 60:
        lines.append(f"… {len(issues) - 60} more")
    return "\n".join(lines)
