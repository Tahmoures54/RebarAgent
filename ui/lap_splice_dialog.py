# ui/lap_splice_dialog.py
"""Lap / splice length calculator dialog (ACI 318, Mabhas 9, Eurocode 2)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from logic.calculator import calculate_lap_splice_detailed
from utils.i18n import t
from utils.logger import setup_logger

logger = setup_logger("RebarAgent.LapSplice")

_STD_LABELS = {
    "ACI318": "ACI 318-19",
    "MABHAS9": "Mabhas 9 (IR)",
    "EC2": "Eurocode 2",
    "SIMPLE": "n × db",
}


class LapSpliceDialog(tk.Toplevel):
    """Code-based lap / splice length calculator."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(t("lap.title"))
        self.geometry("460x460")
        self.minsize(420, 420)
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text=t("lap.standard")).grid(row=0, column=0, sticky="w", pady=4)
        self.std_var = tk.StringVar(value=_STD_LABELS["MABHAS9"])
        std_combo = ttk.Combobox(
            frm, textvariable=self.std_var, state="readonly",
            values=list(_STD_LABELS.values()), width=22,
        )
        std_combo.grid(row=0, column=1, sticky="ew")
        std_combo.bind("<<ComboboxSelected>>", lambda _e: self._toggle_simple())

        ttk.Label(frm, text=t("lap.diameter")).grid(row=1, column=0, sticky="w", pady=4)
        self.dia_var = tk.StringVar(value="16")
        ttk.Entry(frm, textvariable=self.dia_var, width=12).grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text=t("lap.fy")).grid(row=2, column=0, sticky="w", pady=4)
        self.fy_var = tk.StringVar(value="400")
        ttk.Entry(frm, textvariable=self.fy_var, width=12).grid(row=2, column=1, sticky="w")

        ttk.Label(frm, text=t("lap.fc")).grid(row=3, column=0, sticky="w", pady=4)
        self.fc_var = tk.StringVar(value="25")
        ttk.Entry(frm, textvariable=self.fc_var, width=12).grid(row=3, column=1, sticky="w")

        ttk.Label(frm, text=t("lap.multiplier")).grid(row=4, column=0, sticky="w", pady=4)
        self.mult_var = tk.StringVar(value="40")
        self.mult_entry = ttk.Entry(frm, textvariable=self.mult_var, width=12)
        self.mult_entry.grid(row=4, column=1, sticky="w")

        self.top_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text=t("lap.top_bar"), variable=self.top_var).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(8, 2)
        )
        self.epoxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text=t("lap.epoxy"), variable=self.epoxy_var).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=2
        )

        ttk.Button(frm, text=t("lap.calculate"), command=self._calc).grid(
            row=7, column=0, columnspan=2, pady=12
        )

        self.result = tk.StringVar(value="—")
        ttk.Label(frm, textvariable=self.result, font=("Segoe UI", 11, "bold"), wraplength=400).grid(
            row=8, column=0, columnspan=2, sticky="w"
        )
        self.note = tk.StringVar(value="")
        ttk.Label(frm, textvariable=self.note, wraplength=400, foreground="#64748b").grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        ttk.Button(frm, text=t("btn.close"), command=self.destroy).grid(
            row=10, column=0, columnspan=2, pady=8
        )

        self._toggle_simple()
        try:
            self.geometry("+%d+%d" % (parent.winfo_rootx() + 80, parent.winfo_rooty() + 80))
        except Exception:
            pass

    def _selected_standard(self) -> str:
        label = self.std_var.get()
        for code, text in _STD_LABELS.items():
            if text == label:
                return code
        return "ACI318"

    def _toggle_simple(self):
        simple = self._selected_standard() == "SIMPLE"
        state = "normal" if simple else "disabled"
        try:
            self.mult_entry.configure(state=state)
        except Exception:
            pass

    def _calc(self):
        try:
            db = float(self.dia_var.get())
            fy = float(self.fy_var.get())
            fc = float(self.fc_var.get())
            std = self._selected_standard()
            report = calculate_lap_splice_detailed(
                db, fy=fy, fc=fc, standard=std, top_bar=self.top_var.get(),
                epoxy_coated=self.epoxy_var.get(),
                simple_multiplier=float(self.mult_var.get() or 40),
            )
            self.result.set(
                t("lap.result", lap=report.lap_mm, ld=report.ld_mm, cm=report.lap_mm / 10.0)
            )
            self.note.set(report.formula_note)
        except Exception as e:
            logger.error("lap calc: %s", e)
            messagebox.showerror(t("common.error"), str(e), parent=self)
