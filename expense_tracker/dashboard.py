"""
dashboard.py
------------
The Dashboard page: shows total income, total expense, current balance,
a monthly summary, recent transactions, and two embedded Matplotlib
charts (expense pie chart + expense bar chart).
"""

import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import charts
from utils import current_month_year, format_currency


class Card(ttk.Frame):
    """A small rounded 'stat card' used at the top of the dashboard."""

    def __init__(self, parent, title: str, value: str, bootstyle: str = "primary"):
        super().__init__(parent, padding=16, bootstyle=f"{bootstyle}")
        self.title_label = ttk.Label(
            self, text=title, font=("Segoe UI", 10), bootstyle=f"inverse-{bootstyle}"
        )
        self.title_label.pack(anchor="w")
        self.value_label = ttk.Label(
            self, text=value, font=("Segoe UI", 20, "bold"), bootstyle=f"inverse-{bootstyle}"
        )
        self.value_label.pack(anchor="w", pady=(4, 0))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)


class DashboardFrame(ttk.Frame):
    """Main dashboard / home screen shown after login."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app  # reference to the main App controller
        self.db = app.db

        self._build_header()
        self._build_cards()
        self._build_body()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 15))
        ttk.Label(
            header, text="Dashboard", font=("Segoe UI", 18, "bold")
        ).pack(side="left")
        ttk.Button(
            header, text="Refresh", command=self.refresh, bootstyle="secondary-outline"
        ).pack(side="right")

    def _build_cards(self) -> None:
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="x", pady=(0, 15))
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        self.card_income = Card(cards_frame, "Total Income", "0.00", "success")
        self.card_expense = Card(cards_frame, "Total Expense", "0.00", "danger")
        self.card_balance = Card(cards_frame, "Current Balance", "0.00", "info")
        self.card_month = Card(cards_frame, "This Month Spend", "0.00", "warning")

        self.card_income.grid(row=0, column=0, padx=6, sticky="nsew")
        self.card_expense.grid(row=0, column=1, padx=6, sticky="nsew")
        self.card_balance.grid(row=0, column=2, padx=6, sticky="nsew")
        self.card_month.grid(row=0, column=3, padx=6, sticky="nsew")

    def _build_body(self) -> None:
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Left: recent transactions table
        left = ttk.Labelframe(body, text="Recent Transactions", padding=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        columns = ("type", "category_source", "amount", "date")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=14)
        for col, label, width in zip(
            columns, ("Type", "Category / Source", "Amount", "Date"), (70, 160, 100, 100)
        ):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Right: charts (pie + bar) stacked
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.chart_holder_pie = ttk.Labelframe(right, text="Expense Distribution", padding=6)
        self.chart_holder_pie.pack(fill="both", expand=True, pady=(0, 8))

        self.chart_holder_bar = ttk.Labelframe(right, text="Expense by Category", padding=6)
        self.chart_holder_bar.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Reload all summary data, recent transactions and charts."""
        user_id = self.app.current_user.id
        currency_symbol = self.app.currency_symbol()

        total_income = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = ?",
            (user_id,),
        )["total"]
        total_expense = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?",
            (user_id,),
        )["total"]
        balance = total_income - total_expense

        month, year = current_month_year()
        month_spend = self.db.fetch_one(
            """SELECT COALESCE(SUM(amount), 0) AS total FROM expenses
               WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?""",
            (user_id, f"{month:02d}", str(year)),
        )["total"]

        self.card_income.set_value(format_currency(total_income, currency_symbol))
        self.card_expense.set_value(format_currency(total_expense, currency_symbol))
        self.card_balance.set_value(format_currency(balance, currency_symbol))
        self.card_month.set_value(format_currency(month_spend, currency_symbol))

        self._refresh_recent_transactions(user_id)
        self._refresh_charts(user_id)

    def _refresh_recent_transactions(self, user_id: int) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        income_rows = self.db.fetch_all(
            "SELECT amount, source AS label, date FROM income WHERE user_id = ? "
            "ORDER BY date DESC, id DESC LIMIT 10",
            (user_id,),
        )
        expense_rows = self.db.fetch_all(
            "SELECT amount, category AS label, date FROM expenses WHERE user_id = ? "
            "ORDER BY date DESC, id DESC LIMIT 10",
            (user_id,),
        )

        combined = [("Income", r["label"], r["amount"], r["date"]) for r in income_rows]
        combined += [("Expense", r["label"], r["amount"], r["date"]) for r in expense_rows]
        combined.sort(key=lambda r: r[3], reverse=True)

        currency_symbol = self.app.currency_symbol()
        for kind, label, amount, date in combined[:12]:
            self.tree.insert(
                "", "end", values=(kind, label, format_currency(amount, currency_symbol), date)
            )

    def _refresh_charts(self, user_id: int) -> None:
        expense_rows = self.db.fetch_all(
            "SELECT category, amount FROM expenses WHERE user_id = ?", (user_id,)
        )
        category_totals = charts.build_category_totals(expense_rows)
        dark = self.app.is_dark_mode()

        for widget in self.chart_holder_pie.winfo_children():
            widget.destroy()
        for widget in self.chart_holder_bar.winfo_children():
            widget.destroy()

        pie_fig = charts.expense_pie_chart(category_totals, dark)
        pie_canvas = FigureCanvasTkAgg(pie_fig, master=self.chart_holder_pie)
        pie_canvas.draw()
        pie_canvas.get_tk_widget().pack(fill="both", expand=True)

        bar_fig = charts.expense_bar_chart(category_totals, dark)
        bar_canvas = FigureCanvasTkAgg(bar_fig, master=self.chart_holder_bar)
        bar_canvas.draw()
        bar_canvas.get_tk_widget().pack(fill="both", expand=True)
