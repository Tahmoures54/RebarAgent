# logic/calculator.py
"""Basic reinforcement calculations: weight and lap splice length."""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Any, Dict

from config import WEIGHT_COEFFICIENT

logger = logging.getLogger("RebarAgent.Calculator")

SUPPORTED_LAP_STANDARDS = ("ACI318", "MABHAS9", "EC2", "SIMPLE")

_STANDARD_ALIASES = {
    "ACI": "ACI318",
    "ACI318": "ACI318",
    "ACI31819": "ACI318",
    "ACI31814": "ACI318",
    "IR": "MABHAS9",
    "IRAN": "MABHAS9",
    "MABHAS": "MABHAS9",
    "MABHAS9": "MABHAS9",
    "M9": "MABHAS9",
    "ISIRI": "MABHAS9",
    "EC2": "EC2",
    "EC": "EC2",
    "EUROCODE": "EC2",
    "EUROCODE2": "EC2",
    "EN19921": "EC2",
    "EN1992": "EC2",
    "SIMPLE": "SIMPLE",
    "RULEOFTHUMB": "SIMPLE",
    "NXDB": "SIMPLE",
}


@dataclass
class LapSpliceResult:
    lap_mm: float
    ld_mm: float
    standard: str
    formula_note: str
    factors: Dict[str, Any] = field(default_factory=dict)

    def __float__(self) -> float:
        return float(self.lap_mm)


def normalize_lap_standard(standard: str) -> str:
    raw = (standard or "ACI318").strip().upper().replace(" ", "").replace("-", "").replace("_", "")
    mapped = _STANDARD_ALIASES.get(raw)
    if mapped:
        return mapped
    if raw in SUPPORTED_LAP_STANDARDS:
        return raw
    logger.warning("Standard '%s' is not implemented; falling back to ACI 318-19.", standard)
    return "ACI318"


def calculate_weight(dia_mm: float, length_mm: float) -> tuple:
    if dia_mm <= 0 or length_mm < 0:
        raise ValueError("Diameter must be > 0 and length >= 0")
    unit_weight = (dia_mm ** 2) * WEIGHT_COEFFICIENT
    total_weight = unit_weight * (length_mm / 1000.0)
    return unit_weight, total_weight


def calculate_total_weight(dia_mm: float, length_mm: float, quantity: int) -> float:
    if quantity < 0:
        raise ValueError("Quantity must be >= 0")
    _, single = calculate_weight(dia_mm, length_mm)
    return single * quantity


def calculate_lap_splice(
    dia: float, fy: float = 500.0, fc: float = 25.0,
    bar_coating: str = "uncoated", concrete_type: str = "normal",
    top_bar: bool = False, epoxy_coated: bool = False,
    epoxy_cover_sufficient: bool = True, standard: str = "ACI318",
    simple_multiplier: float = 40.0,
) -> float:
    return calculate_lap_splice_detailed(
        dia, fy=fy, fc=fc, bar_coating=bar_coating, concrete_type=concrete_type,
        top_bar=top_bar, epoxy_coated=epoxy_coated,
        epoxy_cover_sufficient=epoxy_cover_sufficient, standard=standard,
        simple_multiplier=simple_multiplier,
    ).lap_mm


def calculate_lap_splice_detailed(
    dia: float, fy: float = 500.0, fc: float = 25.0,
    bar_coating: str = "uncoated", concrete_type: str = "normal",
    top_bar: bool = False, epoxy_coated: bool = False,
    epoxy_cover_sufficient: bool = True, standard: str = "ACI318",
    simple_multiplier: float = 40.0,
) -> LapSpliceResult:
    if fc <= 0 or fy <= 0 or dia <= 0:
        raise ValueError("fc, fy, dia must be positive")
    std = normalize_lap_standard(standard)
    if std == "SIMPLE":
        return _lap_simple(dia, simple_multiplier)
    if std == "EC2":
        return _lap_eurocode2(dia, fy, fc, top_bar, concrete_type)
    if std == "MABHAS9":
        return _lap_mabhas9(
            dia, fy, fc, bar_coating, concrete_type, top_bar,
            epoxy_coated, epoxy_cover_sufficient,
        )
    return _lap_aci318(
        dia, fy, fc, bar_coating, concrete_type, top_bar,
        epoxy_coated, epoxy_cover_sufficient,
    )


def calculate_lap_splice_simple(dia, fc, fy, condition="Tension"):
    top = condition in ("Top", "Tension")
    return calculate_lap_splice(dia, fy=fy, fc=fc, top_bar=top)


def _coating_psi_e(bar_coating: str, epoxy_coated: bool, epoxy_cover_sufficient: bool) -> float:
    is_coated = (bar_coating == "coated") or epoxy_coated
    if not is_coated:
        return 1.0
    return 1.2 if epoxy_cover_sufficient else 1.5


def _lap_simple(dia: float, multiplier: float) -> LapSpliceResult:
    if multiplier <= 0:
        raise ValueError("simple_multiplier must be positive")
    lap = max(float(dia) * float(multiplier), 300.0)
    return LapSpliceResult(
        lap_mm=lap,
        ld_mm=lap,
        standard="SIMPLE",
        formula_note="Site rule: n × db (minimum 300 mm)",
        factors={"n": multiplier, "db": dia},
    )


def _lap_aci318(
    dia: float, fy: float, fc: float, bar_coating: str, concrete_type: str,
    top_bar: bool, epoxy_coated: bool, epoxy_cover_sufficient: bool,
) -> LapSpliceResult:
    psi_t = 1.3 if top_bar else 1.0
    psi_e = _coating_psi_e(bar_coating, epoxy_coated, epoxy_cover_sufficient)
    psi_s = 1.0
    psi_g = fy / 550.0 if fy > 550 else 1.0
    lam = 1.0 if concrete_type == "normal" else 0.85
    denom = (2.1 if dia <= 19 else 1.7) * lam * math.sqrt(fc)
    if denom <= 0:
        raise ValueError("Invalid denominator; check fc and concrete type")
    ld = (fy * psi_t * psi_e * psi_s) / denom * dia * psi_g
    lap = max(1.3 * ld, 300.0)
    return LapSpliceResult(
        lap_mm=lap,
        ld_mm=ld,
        standard="ACI318",
        formula_note="ACI 318-19 simplified ld; class B tension lap = 1.3 ld (min 300 mm)",
        factors={
            "psi_t": psi_t, "psi_e": psi_e, "psi_s": psi_s, "psi_g": psi_g,
            "lambda": lam, "fy": fy, "fc": fc, "db": dia,
        },
    )


def _lap_mabhas9(
    dia: float, fy: float, fc: float, bar_coating: str, concrete_type: str,
    top_bar: bool, epoxy_coated: bool, epoxy_cover_sufficient: bool,
) -> LapSpliceResult:
    """
    Mabhas 9 (1400) tension development is ACI-based.
    Differences applied here: size factor ψs = 0.8 for φ ≤ 20 mm;
    lightweight λ = 0.75; class B lap 1.3 ld; min 300 mm.
    """
    psi_t = 1.3 if top_bar else 1.0
    psi_e = _coating_psi_e(bar_coating, epoxy_coated, epoxy_cover_sufficient)
    psi_s = 0.8 if dia <= 20 else 1.0
    psi_g = fy / 550.0 if fy > 550 else 1.0
    lam = 1.0 if concrete_type == "normal" else 0.75
    denom = (2.1 if dia <= 20 else 1.7) * lam * math.sqrt(fc)
    if denom <= 0:
        raise ValueError("Invalid denominator; check fc and concrete type")
    ld = (fy * psi_t * psi_e * psi_s) / denom * dia * psi_g
    lap = max(1.3 * ld, 300.0)
    return LapSpliceResult(
        lap_mm=lap,
        ld_mm=ld,
        standard="MABHAS9",
        formula_note="Mabhas 9 (1400) ACI-based ld with ψs=0.8 for φ≤20; class B lap 1.3 ld",
        factors={
            "psi_t": psi_t, "psi_e": psi_e, "psi_s": psi_s, "psi_g": psi_g,
            "lambda": lam, "fy": fy, "fc": fc, "db": dia,
        },
    )


def _lap_eurocode2(
    dia: float, fy: float, fc: float, top_bar: bool, concrete_type: str,
) -> LapSpliceResult:
    """EN 1992-1-1 tension lap length (typical >50% lapped in one section)."""
    if fc <= 50:
        fctm = 0.30 * (fc ** (2.0 / 3.0))
    else:
        fctm = 2.12 * math.log(1.0 + (fc + 8.0) / 10.0)
    fctk = 0.7 * fctm
    gamma_c = 1.5
    fctd = 1.0 * fctk / gamma_c
    eta1 = 0.7 if (top_bar or concrete_type != "normal") else 1.0
    eta2 = 1.0 if dia <= 32 else max(0.0, (132.0 - dia) / 100.0)
    fbd = 2.25 * eta1 * eta2 * fctd
    if fbd <= 0:
        raise ValueError("Invalid bond stress fbd; check fc and diameter")
    sigma_sd = fy / 1.15
    lb_rqd = (dia / 4.0) * (sigma_sd / fbd)
    alpha6 = 1.5
    l0 = alpha6 * lb_rqd
    l0_min = max(0.3 * alpha6 * lb_rqd, 15.0 * dia, 200.0)
    lap = max(l0, l0_min)
    return LapSpliceResult(
        lap_mm=lap,
        ld_mm=lb_rqd,
        standard="EC2",
        formula_note="EN 1992-1-1: l0 = α6·lb,rqd (α6=1.5), min max(0.3 α6 lb,rqd, 15φ, 200 mm)",
        factors={
            "fctm": fctm, "fctd": fctd, "fbd": fbd, "eta1": eta1, "eta2": eta2,
            "alpha6": alpha6, "sigma_sd": sigma_sd, "fy": fy, "fc": fc, "db": dia,
        },
    )
