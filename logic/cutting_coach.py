# logic/cutting_coach.py
"""Post-cut advice: leftover reuse, 6 m vs 12 m stock, bankable offcuts."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def coach_from_plan_groups(
    plans_per_group: Dict[Any, Any],
    stock_len: float,
    lang: str = "en",
) -> List[str]:
    """Explainable tips a site engineer can act on before Confirm."""
    total_waste = 0.0
    total_used = 0.0
    bankable = 0
    shorts_on_long_stock = 0
    n_bars = 0
    worst: Tuple[float, str] = (0.0, "")

    for key, data in (plans_per_group or {}).items():
        if not isinstance(key, tuple) or not isinstance(data, dict):
            continue
        dia, grade = key[0], key[1] if len(key) > 1 else ""
        plans = data.get("plans") or []
        pieces: List[float] = []
        group_waste = 0.0
        group_used = 0.0
        for plan in plans:
            bin_items = plan.get("bin") or []
            used = sum(float(L) for L, _rest in bin_items)
            bar = float(plan.get("bar_length") or stock_len)
            waste = max(0.0, bar - used)
            total_waste += waste
            total_used += used
            group_waste += waste
            group_used += used
            n_bars += 1
            if 0.45 <= waste <= 3.2:
                bankable += 1
            for L, _rest in bin_items:
                pieces.append(float(L))
        if pieces and max(pieces) < 5.6 and float(stock_len) >= 11.5:
            shorts_on_long_stock += 1
        if group_used + group_waste > 0:
            wpct = group_waste / (group_used + group_waste)
            if wpct > worst[0]:
                worst = (wpct, f"Ø{dia:g} {grade}")

    if n_bars == 0:
        return []

    util = total_used / (total_used + total_waste) if (total_used + total_waste) else 0.0
    tips: List[str] = []
    fa = lang == "fa"

    if fa:
        tips.append(f"بهره‌وری حدود {util*100:.0f}٪ — {n_bars} شاخه، پرت {total_waste:.2f} متر.")
        if shorts_on_long_stock:
            tips.append("قطعه‌های کوتاه روی شاخه ۱۲ متری نشسته‌اند. یک‌بار با موجودی ۶ متری بهینه کنید؛ اغلب پرت کمتر می‌شود.")
        if bankable:
            tips.append(f"{bankable} ته‌شاخه بین ۰٫۵ تا ۳ متر است. بعد از تأیید، در بانک ضایعات بماند تا پوز بعدی را پر کند.")
        if worst[0] >= 0.18:
            tips.append(f"بیشترین پرت در {worst[1]} ({worst[0]*100:.0f}٪). قطر را جدا ببرید یا طول موجودی را عوض کنید.")
        if util >= 0.92:
            tips.append("طرح خوب است. تأیید کنید تا موجودی و ضایعات به‌روز شود.")
    else:
        tips.append(f"Utilization ~{util*100:.0f}% — {n_bars} bars, {total_waste:.2f} m leftover.")
        if shorts_on_long_stock:
            tips.append("Short pieces landed on 12 m stock. Re-run with 6 m bars in Stock — waste usually drops.")
        if bankable:
            tips.append(f"{bankable} offcut(s) between 0.5–3 m. After Confirm they stay in Scrap Bank for the next listofer.")
        if worst[0] >= 0.18:
            tips.append(f"Highest waste in {worst[1]} ({worst[0]*100:.0f}%). Cut that diameter separately or change stock length.")
        if util >= 0.92:
            tips.append("Plan looks tight. Confirm to lock inventory.")
    return tips[:4]
