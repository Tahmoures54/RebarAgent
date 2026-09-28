# ui/modern_shell.py
"""Main-shell chrome: compact header, metric cards, action rail, workspace."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple


C = {
    "canvas": "#F4F6F8",
    "surface": "#FFFFFF",
    "header": "#0F172A",
    "header_2": "#1E293B",
    "line": "#E2E8F0",
    "line_strong": "#CBD5E1",
    "ink": "#0F172A",
    "ink_soft": "#475569",
    "muted": "#64748B",
    "accent": "#0D9488",
    "accent_soft": "#CCFBF1",
    "accent_ink": "#115E59",
    "ok": "#059669",
    "warn": "#D97706",
}


def configure_premium_styles(style: ttk.Style, theme_key: str = "premium") -> None:
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(".", font=("Segoe UI", 10), background=C["canvas"])
    style.configure("TFrame", background=C["canvas"])
    style.configure("TLabel", background=C["canvas"], foreground=C["ink"])
    style.configure("TLabelframe", background=C["surface"], foreground=C["ink_soft"], relief="flat", borderwidth=1)
    style.configure("TLabelframe.Label", background=C["surface"], foreground=C["muted"], font=("Segoe UI Semibold", 9))
    style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
    style.map("TButton", background=[("active", C["accent_soft"])])
    style.configure("TNotebook", background=C["canvas"])
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=26, background=C["surface"], fieldbackground=C["surface"])
    style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), background=C["canvas"], foreground=C["muted"])

    style.configure(f"{theme_key}.Hero.TFrame", background=C["header"])
    style.configure(f"{theme_key}.Elev.TFrame", background=C["surface"])
    style.configure(f"{theme_key}.Card.TFrame", background=C["surface"])
    style.configure(f"{theme_key}.Soft.TFrame", background=C["canvas"])
    style.configure(f"{theme_key}.HeroTitle.TLabel", background=C["header"], foreground="#F8FAFC", font=("Segoe UI Semibold", 15))
    style.configure(f"{theme_key}.HeroSub.TLabel", background=C["header"], foreground="#94A3B8", font=("Segoe UI", 9))
    style.configure(f"{theme_key}.KPIValue.TLabel", background=C["surface"], foreground=C["ink"], font=("Segoe UI Semibold", 18))
    style.configure(f"{theme_key}.KPILabel.TLabel", background=C["surface"], foreground=C["muted"], font=("Segoe UI", 8))
    style.configure(f"{theme_key}.Rail.TButton", font=("Segoe UI", 10), padding=(14, 9))
    style.configure(f"{theme_key}.Chip.TButton", font=("Segoe UI", 9), padding=(10, 6))
    style.configure(f"{theme_key}.Primary.TButton", font=("Segoe UI Semibold", 10), padding=(14, 9), background=C["accent"], foreground="#FFFFFF")
    style.map(f"{theme_key}.Primary.TButton", background=[("active", "#0F766E")])
    style.configure(f"{theme_key}.Section.TLabelframe", background=C["surface"], foreground=C["ink"])
    style.configure(f"{theme_key}.Section.TLabelframe.Label", background=C["surface"], foreground=C["muted"], font=("Segoe UI Semibold", 9))


class HeroHeader(ttk.Frame):
    def __init__(
        self,
        parent,
        theme_key: str,
        app_name: str = "RebarAgent",
        tagline: str = "BBS  ·  cutting  ·  inventory",
        on_license: Optional[Callable] = None,
        on_dashboard: Optional[Callable] = None,
        on_insights: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(parent, style=f"{theme_key}.Hero.TFrame", **kwargs)
        self.theme_key = theme_key
        self._project_var = tk.StringVar(value="No project")
        self._license_var = tk.StringVar(value="")
        self._build(app_name, tagline, on_license, on_dashboard, on_insights)

    def _build(self, app_name, tagline, on_license, on_dashboard, on_insights):
        tk_key = self.theme_key
        bar = tk.Frame(self, bg=C["header"])
        bar.pack(fill="x")

        left = tk.Frame(bar, bg=C["header"])
        left.pack(side="left", padx=18, pady=12)
        mark = tk.Frame(left, bg=C["accent"], width=3, height=32)
        mark.pack(side="left", padx=(0, 10))
        titles = tk.Frame(left, bg=C["header"])
        titles.pack(side="left")
        tk.Label(titles, text=app_name, bg=C["header"], fg="#F8FAFC", font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(titles, text=tagline, bg=C["header"], fg="#94A3B8", font=("Segoe UI", 9)).pack(anchor="w")

        center = tk.Frame(bar, bg=C["header"])
        center.pack(side="left", expand=True, fill="x", padx=16)
        pill = tk.Frame(center, bg=C["header_2"], padx=14, pady=7)
        pill.pack(anchor="center")
        tk.Label(
            pill,
            textvariable=self._project_var,
            bg=C["header_2"],
            fg="#E2E8F0",
            font=("Segoe UI Semibold", 10),
        ).pack()

        right = tk.Frame(bar, bg=C["header"])
        right.pack(side="right", padx=14, pady=10)
        for label, cmd in (
            ("Dashboard", on_dashboard),
            ("Insights", on_insights),
            ("License", on_license),
        ):
            if not cmd:
                continue
            ttk.Button(right, text=label, command=cmd, style=f"{tk_key}.Chip.TButton").pack(side="left", padx=3)
        tk.Label(
            right,
            textvariable=self._license_var,
            bg=C["header"],
            fg="#5EEAD4",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(10, 0))

    def set_project(self, name: str, client: str = ""):
        if not name:
            self._project_var.set("No project")
        elif client:
            self._project_var.set(f"{name}  ·  {client}")
        else:
            self._project_var.set(name)

    def set_license(self, text: str):
        self._license_var.set(text or "")


class KPIStrip(ttk.Frame):
    def __init__(self, parent, theme_key: str = "premium", **kwargs):
        super().__init__(parent, style=f"{theme_key}.Soft.TFrame", **kwargs)
        self.theme_key = theme_key
        self._vars: Dict[str, tk.StringVar] = {}
        host = tk.Frame(self, bg=C["canvas"])
        host.pack(fill="x", padx=14, pady=(10, 4))
        specs = (
            ("positions", "Positions"),
            ("weight", "Weight"),
            ("listofers", "Listofers"),
            ("stock", "Stock bars"),
            ("health", "Health"),
        )
        for key, label in specs:
            self._add_card(host, key, label)

    def _add_card(self, host, key: str, label: str):
        var = tk.StringVar(value="—")
        self._vars[key] = var
        wrap = tk.Frame(host, bg=C["line"], padx=1, pady=1)
        wrap.pack(side="left", padx=5, fill="x", expand=True)
        card = tk.Frame(wrap, bg=C["surface"], padx=14, pady=10)
        card.pack(fill="both", expand=True)
        tk.Label(card, text=label.upper(), bg=C["surface"], fg=C["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(card, textvariable=var, bg=C["surface"], fg=C["ink"], font=("Segoe UI Semibold", 16)).pack(anchor="w", pady=(2, 0))

    def update_metrics(
        self,
        positions: Any = "—",
        weight: Any = "—",
        listofers: Any = "—",
        stock: Any = "—",
        health: Any = "—",
    ):
        self._vars["positions"].set(str(positions))
        self._vars["weight"].set(str(weight))
        self._vars["listofers"].set(str(listofers))
        self._vars["stock"].set(str(stock))
        self._vars["health"].set(str(health))


class ActionRail(ttk.Frame):
    def __init__(self, parent, theme_key: str, actions: List[Tuple[str, Callable]], **kwargs):
        super().__init__(parent, style=f"{theme_key}.Elev.TFrame", **kwargs)
        self.theme_key = theme_key
        wrap = tk.Frame(self, bg=C["surface"], highlightbackground=C["line"], highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        tk.Label(
            wrap,
            text="WORKSPACE",
            bg=C["surface"],
            fg=C["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=14, pady=(14, 8))
        for i, (text, cmd) in enumerate(actions):
            style = f"{theme_key}.Primary.TButton" if i == 0 else f"{theme_key}.Rail.TButton"
            ttk.Button(wrap, text=text, command=cmd, style=style).pack(fill="x", padx=10, pady=3)
        tk.Frame(wrap, bg=C["surface"]).pack(fill="both", expand=True)


class CommandStrip(ttk.Frame):
    def __init__(self, parent, theme_key: str, actions: List[Tuple[str, Callable]], **kwargs):
        super().__init__(parent, style=f"{theme_key}.Soft.TFrame", **kwargs)
        host = tk.Frame(self, bg=C["canvas"])
        host.pack(fill="x", padx=2, pady=(2, 8))
        for i, (text, cmd) in enumerate(actions):
            ttk.Button(host, text=text, command=cmd, style=f"{theme_key}.Chip.TButton").pack(side="left", padx=3)
            if i in (1, 2):
                tk.Frame(host, bg=C["line_strong"], width=1, height=18).pack(side="left", padx=8)
