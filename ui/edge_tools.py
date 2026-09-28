# ui/edge_tools.py
"""Site-office reports: buy, stock mix, marks, scraps, audit."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from logic.competitive import (
    compare_stock_strategies,
    format_compare_report,
    format_buy_list,
    find_duplicate_marks,
    format_duplicate_report,
)
from logic.site_reports import (
    long_bar_report,
    scrap_match_report,
    weight_roll_report,
    audit_report,
)


class SiteToolsWindow(tk.Toplevel):
    def __init__(self, parent, project_id: int):
        super().__init__(parent)
        self.title("Site tools")
        self.geometry("760x560")
        self.transient(parent)
        self.project_id = project_id
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        tabs = [
            ("Buy list", lambda: format_buy_list(project_id, 12.0)),
            ("6 m vs 12 m", lambda: format_compare_report(compare_stock_strategies(project_id))),
            ("Duplicate marks", lambda: format_duplicate_report(find_duplicate_marks(project_id))),
            ("Long bars", lambda: long_bar_report(project_id)),
            ("Scrap match", lambda: scrap_match_report(project_id)),
            ("Weight roll", lambda: weight_roll_report(project_id)),
            ("Audit", lambda: audit_report(project_id)),
        ]
        for title, loader in tabs:
            self._add_tab(nb, title, loader)
        ttk.Button(self, text="Close", command=self.destroy).pack(anchor="e", padx=10, pady=(0, 10))

    def _add_tab(self, nb, title, loader):
        frame = ttk.Frame(nb, padding=8)
        nb.add(frame, text=title)
        txt = tk.Text(frame, wrap="word", font=("Consolas", 10), height=24)
        txt.pack(fill="both", expand=True)
        try:
            body = loader()
        except Exception as e:
            body = f"Could not build report:\n{e}"
        txt.insert("1.0", body)
        txt.configure(state="disabled")
        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Copy", command=lambda t=body: self._copy(t)).pack(side="left")

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Report copied.", parent=self)
