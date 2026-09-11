# logic/optimizer_cg.py
"""Column-generation optimize_cuts."""
from __future__ import annotations

import threading
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from utils.logger import setup_logger
from logic.optimizer_options import OptimizerOptions
from logic.optimizer_packing import (
    _validate_lengths, _ffd_bins, PULP_AVAILABLE,
)

logger = setup_logger("RebarAgent.OptimizerCG")

try:
    from pulp import LpProblem, LpVariable, LpMinimize, LpMaximize, lpSum, value, PULP_CBC_CMD
except ImportError:
    LpProblem = LpVariable = LpMinimize = LpMaximize = lpSum = value = PULP_CBC_CMD = None


def integer_patterns_to_bins(
    lengths: List[float],
    types_mm: List[int],
    patterns: List[List[int]],
    pattern_counts: List[int],
    scale: int,
    stock_length: float,
) -> List[List[float]]:
    """
    Materialize an integer cutting-stock solution into bins of original lengths.

    Extra pattern copies from '>= demand' constraints are skipped once the pool
    of remaining pieces is empty. Any leftover pieces are packed with FFD.
    """
    pool: Dict[int, List[float]] = defaultdict(list)
    for length in lengths:
        pool[int(round(float(length) * scale))].append(float(length))

    bins: List[List[float]] = []
    for pattern, times in zip(patterns, pattern_counts):
        n_times = int(times or 0)
        if n_times <= 0:
            continue
        for _ in range(n_times):
            needed: List[int] = []
            for i, typ in enumerate(types_mm):
                cnt = int(pattern[i] or 0)
                if cnt > 0:
                    needed.extend([typ] * cnt)
            if not needed:
                continue
            need_counts = Counter(needed)
            if any(len(pool[typ]) < n for typ, n in need_counts.items()):
                # Over-coverage from >= demand — skip unused copies.
                continue
            bins.append([pool[typ].pop() for typ in needed])

    leftover = [piece for pieces in pool.values() for piece in pieces]
    if leftover:
        bins.extend(_ffd_bins(leftover, stock_length))
    return bins


def optimize_cuts(
    lengths: List[float],
    stock_length: float,
    opts: Optional[OptimizerOptions] = None,
    cancel_event: Optional[threading.Event] = None,
) -> List[List[float]]:
    opts = opts or OptimizerOptions()
    err = _validate_lengths(lengths, stock_length)
    if err:
        logger.error("optimize_cuts: %s", err)
        return []
    if cancel_event and cancel_event.is_set():
        return []
    if not PULP_AVAILABLE:
        return _ffd_bins(lengths, stock_length)

    scale = opts.scale_mm
    pieces_mm = [int(round(l * scale)) for l in lengths]
    stock_mm = int(round(stock_length * scale))
    demand = Counter(pieces_mm)
    types = sorted(demand.keys())
    m = len(types)
    if m == 0:
        return []

    patterns: List[List[int]] = []
    for i, L in enumerate(types):
        max_cnt = stock_mm // L
        vec = [0] * m
        vec[i] = int(max_cnt)
        patterns.append(vec)

    prob = LpProblem("CuttingStock_MasterLP", LpMinimize)
    p_vars = [LpVariable(f"p_{j}", lowBound=0, cat="Continuous") for j in range(len(patterns))]
    prob += lpSum(p_vars)
    constr_names: List[str] = []
    for i, L in enumerate(types):
        name = f"demand_{i}"
        prob += lpSum(patterns[j][i] * p_vars[j] for j in range(len(patterns))) >= demand[L], name
        constr_names.append(name)

    for _it in range(opts.max_column_generation_iters):
        if cancel_event and cancel_event.is_set():
            return []
        prob.solve(PULP_CBC_CMD(msg=1 if opts.verbose else 0, timeLimit=max(1, opts.mip_time_limit)))
        dual = []
        for cname in constr_names:
            c = prob.constraints.get(cname)
            dual.append(float(getattr(c, "pi", 0.0) or 0.0))
        sub = LpProblem("CuttingStock_Knapsack", LpMaximize)
        x = [LpVariable(f"x_{i}", lowBound=0, cat="Integer") for i in range(m)]
        sub += lpSum(dual[i] * x[i] for i in range(m))
        sub += lpSum(types[i] * x[i] for i in range(m)) <= stock_mm
        sub.solve(PULP_CBC_CMD(msg=0, timeLimit=max(1, opts.mip_time_limit)))
        sub_val = value(sub.objective) if sub.objective is not None else None
        if sub_val is None or sub_val <= 1.0 + 1e-6:
            break
        new_pat = [int(value(x[i]) or 0) for i in range(m)]
        if sum(new_pat) <= 0:
            break
        patterns.append(new_pat)
        pv = LpVariable(f"p_{len(patterns)-1}", lowBound=0, cat="Continuous")
        p_vars.append(pv)
        for i in range(m):
            prob.constraints[constr_names[i]] += new_pat[i] * pv
        prob.objective += pv

    master_int = LpProblem("CuttingStock_MasterINT", LpMinimize)
    z = [LpVariable(f"Z_{j}", lowBound=0, cat="Integer") for j in range(len(patterns))]
    master_int += lpSum(z)
    for i, L in enumerate(types):
        master_int += lpSum(patterns[j][i] * z[j] for j in range(len(patterns))) >= demand[L], f"dem_{i}"
    if cancel_event and cancel_event.is_set():
        return []
    master_int.solve(PULP_CBC_CMD(msg=1 if opts.verbose else 0, timeLimit=max(1, opts.mip_time_limit)))

    fallback = _ffd_bins(lengths, stock_length)
    try:
        z_counts = [int(round(float(value(zj) or 0))) for zj in z]
    except Exception as e:
        logger.warning("CG integer master unreadable (%s); FFD fallback", e)
        return fallback
    if not any(c > 0 for c in z_counts):
        logger.warning("CG integer master empty; FFD fallback")
        return fallback

    try:
        bins = integer_patterns_to_bins(lengths, types, patterns, z_counts, scale, stock_length)
    except Exception as e:
        logger.warning("CG pattern expand failed (%s); FFD fallback", e)
        return fallback
    packed = sum(len(b) for b in bins)
    if packed != len(lengths):
        logger.warning("CG packing count %s != demand %s; FFD fallback", packed, len(lengths))
        return fallback
    if fallback and len(bins) > len(fallback):
        # Never ship a worse packing than the cheap heuristic.
        return fallback
    return bins or fallback
