# ui/edge_tools.py
"""Buy list, 6 vs 12 comparison, duplicate-mark audit."""
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


class SiteToolsWindow(tk.Toplevel):
    def __init__(self, parent, project_id: int):
        super().__init__(parent)
        self.title("Site tools")
        self.geometry("720x520")
        self.transient(parent)
        self.project_id = project_id
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self._add_tab(nb, "Buy list", self._buy_text)
        self._add_tab(nb, "6 m vs 12 m", self._compare_text)
        self._add_tab(nb, "Duplicate marks", self._dup_text)
        ttk.Button(self, text="Close", command=self.destroy).pack(anchor="e", padx=10, pady=(0, 10))

    def _add_tab(self, nb, title, loader):
        frame = ttk.Frame(nb, padding=8)
        nb.add(frame, text=title)
        txt = tk.Text(frame, wrap="word", font=("Consolas", 10), height=22)
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

    def _buy_text(self) -> str:
        return format_buy_list(self.project_id, 12.0)

    def _compare_text(self) -> str:
        return format_compare_report(compare_stock_strategies(self.project_id))

    def _dup_text(self) -> str:
        return format_duplicate_report(find_duplicate_marks(self.project_id))

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Report copied.", parent=self)
