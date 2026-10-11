"""
budget.py
---------
Budget management screen: set a monthly budget, view remaining budget,
and see a progress bar with color-coded warnings at 75% / 90% / 100%.
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk

from utils import ValidationError, current_month_year, format_currency, validate_amount

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class BudgetFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.db = app.db

        month, year = current_month_year()
        self.month_var = tk.IntVar(value=month)
        self.year_var = tk.IntVar(value=year)
        self.amount_var = tk.StringVar()

        self._build_header()
        self._build_form()
        self._build_progress_section()
        self._build_history_table()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        ttk.Label(self, text="Budget Management", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", pady=(0, 15)
        )

    def _build_form(self) -> None:
        form = ttk.Labelframe(self, text="Set Monthly Budget", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.month_var,
            values=list(range(1, 13)),
            state="readonly",
            width=6,
        ).grid(row=1, column=0, padx=6)

        ttk.Label(form, text="Year").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.year_var, width=8).grid(row=1, column=1, padx=6)

        ttk.Label(form, text="Budget Amount").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.amount_var, width=16).grid(row=1, column=2, padx=6)

        ttk.Button(form, text="Save Budget", bootstyle="success", command=self.save_budget).grid(
            row=1, column=3, padx=10
        )
        ttk.Button(
            form, text="Load Selected Month", bootstyle="secondary-outline", command=self.refresh
        ).grid(row=1, column=4, padx=6)

    def _build_progress_section(self) -> None:
        self.progress_frame = ttk.Labelframe(self, text="Budget Progress", padding=15)
        self.progress_frame.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(self.progress_frame, text="", font=("Segoe UI", 11, "bold"))
        self.status_label.pack(anchor="w", pady=(0, 6))

        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient="horizontal", length=400, mode="determinate", bootstyle="success"
        )
        self.progress_bar.pack(fill="x", pady=(0, 6))

        self.detail_label = ttk.Label(self.progress_frame, text="")
        self.detail_label.pack(anchor="w")

    def _build_history_table(self) -> None:
        ttk.Label(self, text="Budget History", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", pady=(10, 5)
        )
        columns = ("month", "year", "amount")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        for col, label, width in zip(columns, ("Month", "Year", "Budget Amount"), (150, 100, 150)):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def save_budget(self) -> None:
        try:
            amount = validate_amount(self.amount_var.get())
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        month = self.month_var.get()
        year = self.year_var.get()

        existing = self.db.fetch_one(
            "SELECT id FROM budget WHERE user_id = ? AND month = ? AND year = ?",
            (self.app.current_user.id, month, year),
        )
        if existing:
            self.db.execute(
                "UPDATE budget SET amount = ? WHERE id = ?", (amount, existing["id"])
            )
        else:
            self.db.execute(
                "INSERT INTO budget (user_id, month, year, amount) VALUES (?, ?, ?, ?)",
                (self.app.current_user.id, month, year, amount),
            )
        messagebox.showinfo("Success", f"Budget for {MONTH_NAMES[month - 1]} {year} saved.")
        self.refresh()
        self.app.refresh_dashboard()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        month = self.month_var.get()
        year = self.year_var.get()
        symbol = self.app.currency_symbol()

        budget_row = self.db.fetch_one(
            "SELECT amount FROM budget WHERE user_id = ? AND month = ? AND year = ?",
            (self.app.current_user.id, month, year),
        )
        budget_amount = budget_row["amount"] if budget_row else 0.0
        self.amount_var.set(str(budget_amount) if budget_amount else "")

        spent_row = self.db.fetch_one(
            """SELECT COALESCE(SUM(amount), 0) AS total FROM expenses
               WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?""",
            (self.app.current_user.id, f"{month:02d}", str(year)),
        )
        spent = spent_row["total"]
        remaining = budget_amount - spent
        percent = (spent / budget_amount * 100) if budget_amount > 0 else 0

        self.progress_bar["value"] = min(percent, 100)
        if percent >= 100:
            style = "danger"
            status_text = "Budget Exceeded!"
        elif percent >= 90:
            style = "danger"
            status_text = "Warning: 90% of budget used"
        elif percent >= 75:
            style = "warning"
            status_text = "Warning: 75% of budget used"
        else:
            style = "success"
            status_text = "On track"

        self.progress_bar.configure(bootstyle=style)
        self.status_label.configure(text=status_text)
        self.detail_label.configure(
            text=(
                f"Budget: {format_currency(budget_amount, symbol)}   |   "
                f"Spent: {format_currency(spent, symbol)}   |   "
                f"Remaining: {format_currency(remaining, symbol)}   |   "
                f"Used: {percent:.1f}%"
            )
        )

        for row in self.tree.get_children():
            self.tree.delete(row)
        history = self.db.fetch_all(
            "SELECT month, year, amount FROM budget WHERE user_id = ? ORDER BY year DESC, month DESC",
            (self.app.current_user.id,),
        )
        for row in history:
            self.tree.insert(
                "",
                "end",
                values=(MONTH_NAMES[row["month"] - 1], row["year"], format_currency(row["amount"], symbol)),
            )
