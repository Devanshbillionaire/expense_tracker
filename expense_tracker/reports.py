"""
reports.py
----------
Reports screen: generate Daily / Weekly / Monthly / Yearly reports of
income & expenses, view trend charts, and export the current report to
CSV, Excel (.xlsx) or PDF.
"""

import os
from datetime import date, datetime, timedelta

import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import charts
from utils import format_currency

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

REPORT_TYPES = ["Daily", "Weekly", "Monthly", "Yearly"]


class ReportsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.db = app.db
        self.current_dataframe = pd.DataFrame()

        os.makedirs(EXPORTS_DIR, exist_ok=True)

        self._build_header()
        self._build_controls()
        self._build_summary()
        self._build_notebook()
        self.generate_report()

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        ttk.Label(self, text="Reports", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 15))

    def _build_controls(self) -> None:
        controls = ttk.Labelframe(self, text="Report Options", padding=12)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="Report Type").grid(row=0, column=0, sticky="w")
        self.report_type_var = tk.StringVar(value="Monthly")
        ttk.Combobox(
            controls, textvariable=self.report_type_var, values=REPORT_TYPES, state="readonly", width=12
        ).grid(row=1, column=0, padx=6)

        ttk.Label(controls, text="Reference Date (YYYY-MM-DD)").grid(row=0, column=1, sticky="w")
        self.ref_date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(controls, textvariable=self.ref_date_var, width=14).grid(row=1, column=1, padx=6)

        ttk.Button(controls, text="Generate", bootstyle="primary", command=self.generate_report).grid(
            row=1, column=2, padx=10
        )

        ttk.Button(controls, text="Export CSV", bootstyle="secondary", command=self.export_csv).grid(
            row=1, column=3, padx=4
        )
        ttk.Button(controls, text="Export Excel", bootstyle="secondary", command=self.export_excel).grid(
            row=1, column=4, padx=4
        )
        ttk.Button(controls, text="Export PDF", bootstyle="secondary", command=self.export_pdf).grid(
            row=1, column=5, padx=4
        )

    def _build_summary(self) -> None:
        self.summary_label = ttk.Label(self, text="", font=("Segoe UI", 11, "bold"))
        self.summary_label.pack(anchor="w", pady=(0, 10))

    def _build_notebook(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.table_tab = ttk.Frame(self.notebook)
        self.chart_tab_monthly = ttk.Frame(self.notebook)
        self.chart_tab_line = ttk.Frame(self.notebook)
        self.chart_tab_trend = ttk.Frame(self.notebook)

        self.notebook.add(self.table_tab, text="Transactions")
        self.notebook.add(self.chart_tab_monthly, text="Monthly Expense Chart")
        self.notebook.add(self.chart_tab_line, text="Income vs Expense")
        self.notebook.add(self.chart_tab_trend, text="Spending Trend")

        columns = ("type", "amount", "category_source", "date", "extra")
        self.tree = ttk.Treeview(self.table_tab, columns=columns, show="headings", height=16)
        headers = ("Type", "Amount", "Category / Source", "Date", "Payment / Notes")
        widths = (80, 100, 150, 100, 220)
        for col, label, width in zip(columns, headers, widths):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def _date_range(self):
        """Compute (start_date, end_date) as date objects based on report type."""
        try:
            ref = datetime.strptime(self.ref_date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Invalid Date", "Reference date must be in YYYY-MM-DD format.")
            return None, None

        report_type = self.report_type_var.get()
        if report_type == "Daily":
            return ref, ref
        if report_type == "Weekly":
            start = ref - timedelta(days=ref.weekday())
            end = start + timedelta(days=6)
            return start, end
        if report_type == "Monthly":
            start = ref.replace(day=1)
            if ref.month == 12:
                end = ref.replace(day=31)
            else:
                next_month = ref.replace(month=ref.month + 1, day=1)
                end = next_month - timedelta(days=1)
            return start, end
        if report_type == "Yearly":
            return ref.replace(month=1, day=1), ref.replace(month=12, day=31)
        return ref, ref

    def generate_report(self) -> None:
        start, end = self._date_range()
        if start is None:
            return

        user_id = self.app.current_user.id
        income_rows = self.db.fetch_all(
            "SELECT amount, source, date, notes FROM income WHERE user_id = ? AND date BETWEEN ? AND ? "
            "ORDER BY date",
            (user_id, str(start), str(end)),
        )
        expense_rows = self.db.fetch_all(
            "SELECT amount, category, date, payment_method, notes FROM expenses "
            "WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date",
            (user_id, str(start), str(end)),
        )

        symbol = self.app.currency_symbol()
        total_income = sum(r["amount"] for r in income_rows)
        total_expense = sum(r["amount"] for r in expense_rows)
        net = total_income - total_expense

        self.summary_label.configure(
            text=(
                f"Period: {start} to {end}   |   Income: {format_currency(total_income, symbol)}   |   "
                f"Expense: {format_currency(total_expense, symbol)}   |   Net: {format_currency(net, symbol)}"
            )
        )

        # Build a combined dataframe for the table + exports
        records = []
        for r in income_rows:
            records.append(
                {"type": "Income", "amount": r["amount"], "category_source": r["source"],
                 "date": r["date"], "extra": r["notes"] or ""}
            )
        for r in expense_rows:
            records.append(
                {"type": "Expense", "amount": r["amount"], "category_source": r["category"],
                 "date": r["date"], "extra": f"{r['payment_method'] or ''} {r['notes'] or ''}".strip()}
            )
        self.current_dataframe = pd.DataFrame(
            records, columns=["type", "amount", "category_source", "date", "extra"]
        )

        for row in self.tree.get_children():
            self.tree.delete(row)
        for rec in sorted(records, key=lambda r: r["date"]):
            self.tree.insert(
                "", "end",
                values=(rec["type"], format_currency(rec["amount"], symbol), rec["category_source"],
                        rec["date"], rec["extra"]),
            )

        self._refresh_charts(user_id)

    def _refresh_charts(self, user_id: int) -> None:
        dark = self.app.is_dark_mode()

        # Monthly expense bar chart (last 12 months of data)
        monthly_rows = self.db.fetch_all(
            """SELECT strftime('%Y-%m', date) AS ym, SUM(amount) AS total FROM expenses
               WHERE user_id = ? GROUP BY ym ORDER BY ym""",
            (user_id,),
        )
        monthly_totals = {r["ym"]: r["total"] for r in monthly_rows}

        # Income vs expense per month
        income_monthly = self.db.fetch_all(
            """SELECT strftime('%Y-%m', date) AS ym, SUM(amount) AS total FROM income
               WHERE user_id = ? GROUP BY ym ORDER BY ym""",
            (user_id,),
        )
        income_by_month = {r["ym"]: r["total"] for r in income_monthly}
        all_months = sorted(set(monthly_totals) | set(income_by_month))
        income_values = [income_by_month.get(m, 0) for m in all_months]
        expense_values = [monthly_totals.get(m, 0) for m in all_months]

        # Spending trend (daily totals across current report range)
        trend_rows = self.db.fetch_all(
            "SELECT date, SUM(amount) AS total FROM expenses WHERE user_id = ? GROUP BY date ORDER BY date",
            (user_id,),
        )
        trend_dates = [r["date"] for r in trend_rows][-30:]
        trend_amounts = [r["total"] for r in trend_rows][-30:]

        for holder, fig in (
            (self.chart_tab_monthly, charts.monthly_expense_bar_chart(monthly_totals, dark)),
            (self.chart_tab_line, charts.income_vs_expense_line_chart(all_months, income_values, expense_values, dark)),
            (self.chart_tab_trend, charts.spending_trend_chart(trend_dates, trend_amounts, dark)),
        ):
            for widget in holder.winfo_children():
                widget.destroy()
            canvas = FigureCanvasTkAgg(fig, master=holder)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def export_csv(self) -> None:
        if self.current_dataframe.empty:
            messagebox.showwarning("No Data", "Nothing to export for the selected period.")
            return
        path = filedialog.asksaveasfilename(
            initialdir=EXPORTS_DIR, defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        self.current_dataframe.to_csv(path, index=False)
        messagebox.showinfo("Exported", f"Report exported to:\n{path}")

    def export_excel(self) -> None:
        if self.current_dataframe.empty:
            messagebox.showwarning("No Data", "Nothing to export for the selected period.")
            return
        path = filedialog.asksaveasfilename(
            initialdir=EXPORTS_DIR, defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")]
        )
        if not path:
            return
        self.current_dataframe.to_excel(path, index=False, engine="openpyxl")
        messagebox.showinfo("Exported", f"Report exported to:\n{path}")

    def export_pdf(self) -> None:
        if self.current_dataframe.empty:
            messagebox.showwarning("No Data", "Nothing to export for the selected period.")
            return
        path = filedialog.asksaveasfilename(
            initialdir=EXPORTS_DIR, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(path, pagesize=A4)
        elements = [
            Paragraph("Personal Expense Tracker - Report", styles["Title"]),
            Paragraph(self.summary_label.cget("text"), styles["Normal"]),
            Spacer(1, 16),
        ]

        data = [list(self.current_dataframe.columns)] + self.current_dataframe.astype(str).values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C6FFF")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F0F5")]),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)
        messagebox.showinfo("Exported", f"Report exported to:\n{path}")
