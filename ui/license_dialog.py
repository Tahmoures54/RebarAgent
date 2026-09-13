# ui/license_dialog.py
"""License status + self-serve USDT (TRC20) checkout. Payment is verified
on-chain; the app issues and applies the activation key without WhatsApp.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from config import THEMES, AppTheme, APP_NAME, PURCHASE_CONTACT
from utils.i18n import t
from utils.license import get_license_info, get_machine_id, activate_license, format_license_status
from utils.usdt_payment import (
    build_invoice,
    fulfill_paid_plan,
    get_checkout_plan,
    get_usdt_receive_address,
    is_valid_tron_address,
    list_checkout_plans,
)


class LicenseDialog(tk.Toplevel):
    def __init__(self, master, db, callback=None):
        super().__init__(master)
        self.master_app = master
        self.db = db
        self.callback = callback
        self._busy = False

        state_obj = getattr(master, "state", None)
        if callable(state_obj) or state_obj is None:
            theme = AppTheme.TURQUOISE
        else:
            theme = getattr(state_obj, "theme", AppTheme.TURQUOISE)
        theme_key = getattr(theme, "value", theme)
        colors = THEMES.get(theme_key) or THEMES[AppTheme.TURQUOISE.value]
        self.bg = colors["bg"]
        self.fg = colors["fg"]
        self.accent = colors["accent"]
        self.button_style = f"{theme_key}.TButton"

        self.title(t("lic.title", app=APP_NAME))
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()
        self.configure(bg=self.bg)
        self.geometry("640x760")
        self.minsize(560, 560)
        self._center_on_screen(640, 760)

        self.lic_info = get_license_info(self.db)
        self.lic_type = self.lic_info.get("type", "trial")
        self.plan_var = tk.StringVar(value="pro_1y")
        self.key_var = tk.StringVar()
        self.txid_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")
        self._addr_var = tk.StringVar()
        self._amt_var = tk.StringVar()
        self._invoice_labels = {}
        self._build_ui()
        if self.lic_type != "unlimited":
            self._refresh_invoice()

    def _center_on_screen(self, w, h):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.geometry(f"+{x}+{y}")

    def _scroll_inner(self):
        wrapper = tk.Frame(self, bg=self.bg)
        wrapper.pack(fill="both", expand=True)
        canvas = tk.Canvas(wrapper, bg=self.bg, highlightthickness=0)
        vsb = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.bg, padx=28, pady=16)
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)

        def _stretch(_event=None):
            canvas.itemconfigure(win, width=canvas.winfo_width())

        canvas.bind("<Configure>", _stretch)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _linux_up(_event):
            canvas.yview_scroll(-1, "units")

        def _linux_down(_event):
            canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _wheel)
        canvas.bind_all("<Button-4>", _linux_up)
        canvas.bind_all("<Button-5>", _linux_down)
        self.bind("<Destroy>", lambda _e: self._unbind_scroll())
        self._scroll_canvas = canvas
        return inner

    def _unbind_scroll(self):
        try:
            self._scroll_canvas.unbind_all("<MouseWheel>")
            self._scroll_canvas.unbind_all("<Button-4>")
            self._scroll_canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    def _build_ui(self):
        header = tk.Frame(self, bg=self.accent, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text=t("lic.header"),
            font=("Segoe UI", 16, "bold"), fg="white", bg=self.accent,
        ).pack(pady=12)

        main = self._scroll_inner()

        status_text = format_license_status(self.db)
        trial_days = self.lic_info.get("remaining_days", None)
        status_frame = tk.Frame(main, bg=self.bg)
        status_frame.pack(fill="x", pady=5)
        tk.Label(
            status_frame, text=t("lic.status_label"),
            font=("Arial", 10, "bold"), fg=self.fg, bg=self.bg,
        ).pack(side="left")
        tk.Label(
            status_frame, text=f" {status_text}",
            font=("Arial", 10), fg=self.fg, bg=self.bg,
        ).pack(side="left", padx=5)
        if trial_days is not None and self.lic_type != "unlimited":
            try:
                trial_days = int(trial_days)
            except (ValueError, TypeError):
                trial_days = 0
            if trial_days > 0:
                days_color = "red" if trial_days <= 3 else "orange"
                tk.Label(
                    status_frame, text=t("lic.days_left", days=trial_days),
                    font=("Arial", 10, "bold"), fg=days_color, bg=self.bg,
                ).pack(side="left")

        if self.lic_type == "unlimited":
            tk.Label(
                main, text=t("lic.full_version"),
                font=("Arial", 11), fg="green", bg=self.bg, justify="center",
            ).pack(pady=20)
            ttk.Button(main, text=t("btn.close"), command=self.destroy, style=self.button_style).pack(pady=10)
            return

        card_bg = "#f0f4fa" if self.bg == "white" else "#2a2d34"
        pay_card = tk.Frame(main, bg=card_bg, padx=15, pady=12)
        pay_card.pack(fill="x", pady=(12, 8))
        tk.Label(
            pay_card, text=t("lic.self_serve_title"),
            font=("Arial", 12, "bold"), fg=self.accent, bg=card_bg,
        ).pack(anchor="w")
        tk.Label(
            pay_card, text=t("lic.self_serve_body"),
            font=("Arial", 9), fg=self.fg, bg=card_bg, wraplength=540, justify="left",
        ).pack(anchor="w", pady=(4, 8))

        tk.Label(
            pay_card, text=t("lic.choose_plan"),
            font=("Arial", 10, "bold"), fg=self.fg, bg=card_bg,
        ).pack(anchor="w", pady=(4, 4))

        for plan in list_checkout_plans():
            days_txt = t("lic.lifetime") if plan.days is None else t("lic.days", days=plan.days)
            seats = t("lic.seats", n=plan.seats) if plan.seats else ""
            name = plan.name_fa if _is_fa() else plan.name_en
            label = t("lic.plan_row", name=name, days=days_txt, seats=seats, usd=plan.price_usd)
            tk.Radiobutton(
                pay_card,
                text=label,
                value=plan.sku,
                variable=self.plan_var,
                command=self._refresh_invoice,
                bg=card_bg,
                fg=self.fg,
                selectcolor=card_bg,
                activebackground=card_bg,
                activeforeground=self.fg,
                highlightthickness=0,
                anchor="w",
                font=("Arial", 10),
            ).pack(anchor="w", pady=1)

        inv = tk.Frame(pay_card, bg=card_bg)
        inv.pack(fill="x", pady=(10, 4))

        self._invoice_labels["warn"] = tk.Label(
            inv, text="", font=("Arial", 9, "bold"), fg="#b00020", bg=card_bg,
            wraplength=540, justify="left",
        )
        self._invoice_labels["warn"].pack(anchor="w")

        row_addr = tk.Frame(inv, bg=card_bg)
        row_addr.pack(fill="x", pady=3)
        tk.Label(row_addr, text=t("lic.address"), font=("Arial", 9, "bold"), fg=self.fg, bg=card_bg).pack(anchor="w")
        addr_line = tk.Frame(row_addr, bg=card_bg)
        addr_line.pack(fill="x")
        addr_entry = ttk.Entry(addr_line, textvariable=self._addr_var, width=42, state="readonly")
        addr_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(addr_line, text=t("lic.copy"), command=self._copy_address, style=self.button_style).pack(side="left")

        row_amt = tk.Frame(inv, bg=card_bg)
        row_amt.pack(fill="x", pady=3)
        tk.Label(row_amt, text=t("lic.amount"), font=("Arial", 9, "bold"), fg=self.fg, bg=card_bg).pack(anchor="w")
        amt_line = tk.Frame(row_amt, bg=card_bg)
        amt_line.pack(fill="x")
        amt_entry = ttk.Entry(amt_line, textvariable=self._amt_var, width=24, state="readonly")
        amt_entry.pack(side="left", padx=(0, 6))
        ttk.Button(amt_line, text=t("lic.copy"), command=self._copy_amount, style=self.button_style).pack(side="left")

        tk.Label(
            inv, text=t("lic.network_warn"),
            font=("Arial", 8), fg="gray", bg=card_bg, wraplength=540, justify="left",
        ).pack(anchor="w", pady=(6, 2))

        tx_row = tk.Frame(inv, bg=card_bg)
        tx_row.pack(fill="x", pady=(8, 4))
        tk.Label(tx_row, text=t("lic.txid_optional"), font=("Arial", 8), fg=self.fg, bg=card_bg).pack(side="left")
        ttk.Entry(tx_row, textvariable=self.txid_var, width=28).pack(side="left", padx=6)

        self.check_btn = tk.Button(
            inv,
            text=t("lic.i_paid"),
            font=("Arial", 11, "bold"),
            bg="#16a34a", fg="white",
            activebackground="#15803d", activeforeground="white",
            relief="flat", bd=0, padx=18, pady=10,
            cursor="hand2",
            command=self._check_payment,
        )
        self.check_btn.pack(anchor="w", pady=(8, 4))

        tk.Label(
            inv, textvariable=self.status_var,
            font=("Arial", 9), fg=self.fg, bg=card_bg, wraplength=540, justify="left",
        ).pack(anchor="w")

        mid_label = tk.Frame(main, bg=self.bg)
        mid_label.pack(fill="x", pady=(15, 2))
        tk.Label(
            mid_label, text=t("lic.machine_id"),
            font=("Arial", 10, "bold"), fg=self.fg, bg=self.bg,
        ).pack(anchor="w")

        mid_frame = tk.Frame(main, bg=self.bg)
        mid_frame.pack(fill="x")
        mid = get_machine_id()
        mid_entry = ttk.Entry(mid_frame, width=38, state="readonly")
        mid_entry.pack(side="left", padx=(0, 5))
        mid_entry.configure(state="normal")
        mid_entry.insert(0, mid)
        mid_entry.configure(state="readonly")

        def copy_mid():
            self.clipboard_clear()
            self.clipboard_append(mid)
            messagebox.showinfo(t("common.info"), t("lic.mid_copied"), parent=self)

        ttk.Button(mid_frame, text=t("lic.copy"), command=copy_mid, style=self.button_style).pack(side="left")

        ttk.Separator(main, orient="horizontal").pack(fill="x", pady=15)

        activate_header = tk.Frame(main, bg=self.bg)
        activate_header.pack(fill="x", pady=(0, 10))
        tk.Label(
            activate_header, text=t("lic.have_key"),
            font=("Arial", 10, "bold"), fg=self.fg, bg=self.bg,
        ).pack(anchor="w")

        key_frame = tk.Frame(main, bg=self.bg)
        key_frame.pack(fill="x", pady=(0, 5))
        tk.Label(key_frame, text=t("lic.activation_key"), font=("Arial", 9), fg=self.fg, bg=self.bg).pack(side="left")
        ttk.Entry(key_frame, textvariable=self.key_var, width=32).pack(side="left", padx=5)
        ttk.Button(key_frame, text=t("lic.paste"), command=self._paste_code, style=self.button_style).pack(side="left")

        btn_row = tk.Frame(main, bg=self.bg)
        btn_row.pack(fill="x", pady=(10, 5))
        ttk.Button(btn_row, text=t("lic.activate_now"), command=self._activate, style=self.button_style).pack(
            side="left", padx=(0, 15)
        )
        ttk.Button(btn_row, text=t("btn.close"), command=self.destroy, style=self.button_style).pack(side="left")

        ttk.Separator(main, orient="horizontal").pack(fill="x", pady=15)
        tk.Label(main, text=t("lic.help"), font=("Arial", 9, "bold"), fg=self.fg, bg=self.bg, anchor="w").pack(anchor="w")
        wa = tk.Label(
            main, text=t("lic.whatsapp", phone=PURCHASE_CONTACT["whatsapp"]),
            font=("Arial", 9), fg="#2563eb", bg=self.bg, anchor="w", cursor="hand2",
        )
        wa.pack(anchor="w")
        wa.bind("<Button-1>", lambda _e: webbrowser.open(f"https://wa.me/{PURCHASE_CONTACT['whatsapp_digits']}"))
        worker = (PURCHASE_CONTACT.get("worker_url") or "").strip()
        if worker:
            tk.Label(main, text=worker, font=("Arial", 9), fg="#2563eb", bg=self.bg, cursor="hand2").pack(anchor="w")

    def _refresh_invoice(self):
        if not hasattr(self, "_addr_var"):
            return
        sku = self.plan_var.get()
        plan = get_checkout_plan(sku)
        addr = get_usdt_receive_address()
        if plan is None:
            return
        try:
            invoice = build_invoice(sku, get_machine_id(), address=addr)
        except ValueError:
            return
        self._addr_var.set(invoice.address or t("lic.address_missing"))
        self._amt_var.set(f"{invoice.amount_usdt} USDT")
        warn = ""
        if not addr:
            warn = t("lic.not_configured")
        elif not is_valid_tron_address(addr):
            warn = t("lic.bad_address")
        if self._invoice_labels.get("warn"):
            self._invoice_labels["warn"].configure(text=warn)
        if hasattr(self, "check_btn"):
            self.check_btn.configure(state=("disabled" if warn else "normal"))

    def _copy_address(self):
        text = self._addr_var.get().strip()
        if not text or text == t("lic.address_missing"):
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set(t("lic.copied_address"))

    def _copy_amount(self):
        text = (self._amt_var.get() or "").replace(" USDT", "").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set(t("lic.copied_amount"))

    def _check_payment(self):
        if self._busy:
            return
        warn = self._invoice_labels.get("warn")
        if warn and warn.cget("text"):
            messagebox.showwarning(t("common.warning"), warn.cget("text"), parent=self)
            return
        sku = self.plan_var.get()
        txid = self.txid_var.get().strip() or None
        self._busy = True
        self.check_btn.configure(state="disabled")
        self.status_var.set(t("lic.checking"))

        def work():
            try:
                ok, msg, key, paid_tx = fulfill_paid_plan(
                    self.db, sku, get_machine_id(), txid=txid,
                )
                err = None
            except Exception as exc:
                ok, msg, key, paid_tx, err = False, str(exc), None, None, exc
            self.after(0, lambda: self._on_check_done(ok, msg, key, paid_tx, err))

        threading.Thread(target=work, daemon=True).start()

    def _on_check_done(self, ok, msg, key, paid_tx, err):
        self._busy = False
        self.check_btn.configure(state="normal")
        if err is not None:
            self.status_var.set(t("lic.lookup_failed", err=msg))
            messagebox.showerror(t("common.error"), t("lic.lookup_failed", err=msg), parent=self)
            return
        if ok:
            self.status_var.set(t("lic.paid_ok", tx=(paid_tx or "")[:18]))
            messagebox.showinfo(t("common.success"), t("lic.activated"), parent=self)
            if self.callback:
                self.callback()
            self.destroy()
            return
        friendly = {
            "payment_not_found": t("lic.payment_not_found"),
            "usdt_not_configured": t("lic.not_configured"),
            "usdt_bad_address": t("lic.bad_address"),
            "unknown_plan": t("lic.unknown_plan"),
        }
        text = friendly.get(msg, msg)
        if isinstance(msg, str) and msg.startswith("lookup_failed:"):
            text = t("lic.lookup_failed", err=msg.split(":", 1)[-1])
        self.status_var.set(text)
        messagebox.showwarning(t("lic.not_yet"), text, parent=self)

    def _paste_code(self):
        try:
            clipboard_text = self.clipboard_get()
            self.key_var.set(clipboard_text.strip())
        except tk.TclError:
            messagebox.showwarning(t("common.warning"), t("lic.clipboard_empty"), parent=self)

    def _activate(self):
        code = self.key_var.get().strip()
        if not code:
            messagebox.showwarning(t("common.warning"), t("lic.missing_key"), parent=self)
            return
        success, message = activate_license(code, self.db)
        if success:
            messagebox.showinfo(t("common.success"), t("lic.activated"), parent=self)
            if self.callback:
                self.callback()
            self.destroy()
        else:
            messagebox.showerror(t("lic.activate_failed"), message, parent=self)


def _is_fa() -> bool:
    from utils.i18n import get_language
    return get_language() == "fa"
