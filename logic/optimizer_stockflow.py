# logic/optimizer_stockflow.py
"""Multi-stock packing and scrap+stock orchestration."""
from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
from collections import defaultdict
import threading, hashlib, json, sqlite3
from config import DEFAULT_REBAR_GRADE, DB_PATH
from utils.logger import setup_logger
from logic.optimizer_options import OptimizerOptions
from logic.optimizer_packing import _best_fit_decreasing, _pack_one_bar_ffd, _pack_all_single_stock
from logic.optimizer_metrics import get_scrap_infos_for_dia_grade, get_available_stock_bars

logger = setup_logger("RebarAgent.OptimizerStockflow")


def optimize_remaining_multi_stock(items, stock_lengths_qty, default_stock_length, opts=None, cancel_event=None):
    opts=opts or OptimizerOptions()
    if not items: return [], []
    pool={float(L):int(q) for L,q in (stock_lengths_qty or {}).items() if L and q and q>0}
    if not pool: return _pack_all_single_stock(items,default_stock_length,opts,cancel_event,stock_limit=None)
    remaining=sorted(items,key=lambda x:x[0],reverse=True); plans=[]; new_scraps=[]; seq=1; kerf=opts.kerf_m or 0.0; min_scrap=opts.min_usable_scrap_m or 0.0
    guard=0
    while remaining and guard<max(500,len(items)*3):
        guard+=1
        if cancel_event and cancel_event.is_set(): break
        longest=remaining[0][0]; candidates=[L for L,q in pool.items() if q>0 and L+1e-9>=longest]
        if not candidates:
            if opts.allow_stock_overuse and default_stock_length>=longest-1e-9:
                candidates=[float(default_stock_length)]; pool.setdefault(float(default_stock_length),10**9)
            else: break
        best_L=best_packed=best_still=None; best_score=-1.0
        for L in candidates:
            packed,still,_=_pack_one_bar_ffd(remaining,L,kerf)
            if not packed: continue
            cut=sum(x[0] for x in packed); score=(cut/L if L>0 else 0)*1000-L*0.001
            if score>best_score: best_score,best_L,best_packed,best_still=score,L,packed,still
        if not best_packed or best_L is None: break
        plans.append({"bin":best_packed,"bar_length":best_L,"scrap_id":None,"stock_seq":seq}); seq+=1
        waste=max(0.0,best_L-sum(x[0] for x in best_packed))
        if waste>=min_scrap-1e-9 and waste>1e-6: new_scraps.append(round(waste,6))
        remaining=best_still if best_still is not None else []
        if best_L in pool: pool[best_L]=max(0,pool[best_L]-1)
    return plans,new_scraps


def optimize_with_scraps_and_stock(project_id,diameter,grade,items,stock_length,opts=None,cancel_event=None):
    opts=opts or OptimizerOptions(); scrap_infos=get_scrap_infos_for_dia_grade(project_id,diameter,grade); stock_counts=get_available_stock_bars(project_id,diameter,grade)
    scrap_plans,remaining=_best_fit_decreasing(items,scrap_infos)
    if bool(opts.use_multi_stock) and stock_counts and remaining:
        stock_map=dict(stock_counts)
        if opts.allow_stock_overuse:
            stock_map.setdefault(float(stock_length),stock_map.get(float(stock_length),0))
            if stock_map.get(float(stock_length),0)<=0: stock_map[float(stock_length)]=10**6
        stock_plans,new_scraps=optimize_remaining_multi_stock(remaining,stock_map,stock_length,opts,cancel_event)
    else:
        stock_limit=next((qty for sl,qty in stock_counts.items() if abs(sl-stock_length)<1e-6),None)
        stock_plans,new_scraps=_pack_all_single_stock(remaining,stock_length,opts,cancel_event,stock_limit)
    usage=defaultdict(int)
    for p in stock_plans: usage[round(float(p.get("bar_length") or stock_length),6)]+=1
    return scrap_plans+stock_plans,new_scraps,dict(usage)


def compute_plan_data_hash(project_id,listofer_filter,stock_length,data_by_key):
    h=hashlib.sha256(); h.update(f"{project_id}|{listofer_filter}|{stock_length}".encode())
    for (dia,grade),items in sorted(data_by_key.items(),key=lambda x:(x[0][0],x[0][1])):
        for length,label in sorted(items,key=lambda x:(x[0],json.dumps(x[1],sort_keys=True))): h.update(f"{dia}|{grade}|{length}|{json.dumps(label,sort_keys=True)}".encode())
    return h.hexdigest()


def _resolve_stock_source_id(conn,project_id,plan):
    """Resolve a real stock.id; stock_seq is never persisted as an identity."""
    length=float(plan.get("bar_length") or 0.0); diameter=plan.get("diameter") or plan.get("dia"); grade=plan.get("grade")
    for _,label in plan.get("bin") or []:
        if isinstance(label,dict):
            diameter=label.get("diameter") or label.get("dia") or diameter; grade=label.get("grade") or grade
            if diameter is not None: break
    if length<=0 or diameter is None: raise ValueError("stock plan lacks physical source dimensions")
    params=[project_id,float(diameter),length]; sql="SELECT id FROM stock WHERE project_id=? AND diameter=? AND ABS(length-?)<0.000001"
    if grade is not None: sql+=" AND grade=?"; params.append(grade)
    row=conn.execute(sql+" ORDER BY id LIMIT 1",params).fetchone()
    if not row: raise ValueError(f"stock source not found for diameter={diameter}, length={length}, grade={grade}")
    return int(row[0])


def store_cutting_assignments(project_id,listofer_number,plans,rebar_id_map):
    """Persist idempotent rebar-to-source assignments with real source IDs."""
    conn=sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys=ON"); rows=[]; seen=set()
        for plan in plans or []:
            if not isinstance(plan,dict): continue
            source_type="scrap" if plan.get("scrap_id") is not None else "stock"
            source_id=int(plan["scrap_id"]) if source_type=="scrap" else _resolve_stock_source_id(conn,project_id,plan)
            for _,label in plan.get("bin") or []:
                item_idx=label.get("item_idx") if isinstance(label,dict) else None
                if item_idx is None: continue
                rebar_id=rebar_id_map.get(item_idx)
                if rebar_id is None: continue
                rebar_id=int(rebar_id); key=(project_id,str(listofer_number),rebar_id)
                if key in seen: continue
                seen.add(key)
                existing=conn.execute("SELECT source_type,source_id FROM cutting_assignments WHERE project_id=? AND listofer_number=? AND rebar_id=?",(project_id,listofer_number,rebar_id)).fetchone()
                if existing:
                    if existing[0]!=source_type or int(existing[1])!=source_id: raise ValueError(f"rebar {rebar_id} is already assigned to {existing[0]}#{existing[1]}; refusing reassignment")
                    continue
                rows.append((project_id,listofer_number,rebar_id,source_type,source_id))
        if rows: conn.executemany("INSERT INTO cutting_assignments (project_id,listofer_number,rebar_id,source_type,source_id) VALUES (?,?,?,?,?)",rows)
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()
