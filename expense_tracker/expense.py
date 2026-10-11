"""
expense.py
----------
Expense management screen: add, edit, delete, search and filter expenses.

Fields: Amount, Category, Date, Payment Method, Notes
Also triggers budget warning notifications (75% / 90% / 100%) whenever
a new expense pushes the current month's spend past a threshold.
"""

import json
import tkinter as tk
from datetime import date
from tkinter import messagebox
import ttkbootstrap as ttk

from utils import (
    EXPENSE_CATEGORIES,
    PAYMENT_METHODS,
    ValidationError,
    format_currency,
    validate_amount,
    validate_date,
    validate_not_empty,
)


class ExpenseFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.db = app.db
        self.selected_id = None

        self._build_header()
        self._build_form()
        self._build_filter_bar()
        self._build_table()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        ttk.Label(self, text="Expense Management", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", pady=(0, 15)
        )

    def _build_form(self) -> None:
        form = ttk.Labelframe(self, text="Add / Edit Expense", padding=12)
        form.pack(fill="x", pady=(0, 10))
        for i in range(5):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Amount").grid(row=0, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_var).grid(row=1, column=0, sticky="ew", padx=4)

        ttk.Label(form, text="Category").grid(row=0, column=1, sticky="w")
        self.category_var = tk.StringVar(value=EXPENSE_CATEGORIES[0])
        ttk.Combobox(
            form, textvariable=self.category_var, values=EXPENSE_CATEGORIES, state="readonly"
        ).grid(row=1, column=1, sticky="ew", padx=4)

        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w")
        self.date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(form, textvariable=self.date_var).grid(row=1, column=2, sticky="ew", padx=4)

        ttk.Label(form, text="Payment Method").grid(row=0, column=3, sticky="w")
        self.payment_var = tk.StringVar(value=PAYMENT_METHODS[0])
        ttk.Combobox(
            form, textvariable=self.payment_var, values=PAYMENT_METHODS, state="readonly"
        ).grid(row=1, column=3, sticky="ew", padx=4)

        ttk.Label(form, text="Notes").grid(row=0, column=4, sticky="w")
        self.notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.notes_var).grid(row=1, column=4, sticky="ew", padx=4)

        btn_row = ttk.Frame(form)
        btn_row.grid(row=2, column=0, columnspan=5, pady=(10, 0), sticky="w")
        ttk.Button(btn_row, text="Add Expense", bootstyle="success", command=self.add_expense).pack(
            side="left", padx=4
        )
        ttk.Button(
            btn_row, text="Update Selected", bootstyle="info", command=self.update_expense
        ).pack(side="left", padx=4)
        ttk.Button(
            btn_row, text="Delete Selected", bootstyle="danger", command=self.delete_expense
        ).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Form", bootstyle="secondary-outline", command=self.clear_form).pack(
            side="left", padx=4
        )

    def _build_filter_bar(self) -> None:
        filter_frame = ttk.Labelframe(self, text="Search & Filter", padding=10)
        filter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_frame, text="Keyword").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_var, width=16).grid(row=1, column=0, padx=4)

        ttk.Label(filter_frame, text="Category").grid(row=0, column=1, sticky="w")
        self.filter_category_var = tk.StringVar(value="All")
        ttk.Combobox(
            filter_frame,
            textvariable=self.filter_category_var,
            values=["All"] + EXPENSE_CATEGORIES,
            state="readonly",
            width=14,
        ).grid(row=1, column=1, padx=4)

        ttk.Label(filter_frame, text="Month (1-12)").grid(row=0, column=2, sticky="w")
        self.filter_month_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_month_var, width=10).grid(row=1, column=2, padx=4)

        ttk.Label(filter_frame, text="Year").grid(row=0, column=3, sticky="w")
        self.filter_year_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_year_var, width=10).grid(row=1, column=3, padx=4)

        ttk.Label(filter_frame, text="Min Amount").grid(row=0, column=4, sticky="w")
        self.filter_min_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_min_var, width=10).grid(row=1, column=4, padx=4)

        ttk.Label(filter_frame, text="Max Amount").grid(row=0, column=5, sticky="w")
        self.filter_max_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_max_var, width=10).grid(row=1, column=5, padx=4)

        ttk.Button(filter_frame, text="Apply", bootstyle="primary", command=self.refresh).grid(
            row=1, column=6, padx=8
        )
        ttk.Button(
            filter_frame, text="Reset", bootstyle="secondary-outline", command=self._reset_filters
        ).grid(row=1, column=7, padx=4)

    def _reset_filters(self) -> None:
        self.search_var.set("")
        self.filter_category_var.set("All")
        self.filter_month_var.set("")
        self.filter_year_var.set("")
        self.filter_min_var.set("")
        self.filter_max_var.set("")
        self.refresh()

    def _build_table(self) -> None:
        columns = ("id", "amount", "category", "date", "payment", "notes")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=13)
        headers = ("ID", "Amount", "Category", "Date", "Payment", "Notes")
        widths = (40, 100, 110, 100, 110, 220)
        for col, label, width in zip(columns, headers, widths):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ------------------------------------------------------------------
    def _on_row_select(self, event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_id = int(values[0])
        self.amount_var.set(values[1].replace(self.app.currency_symbol(), "").replace(",", ""))
        self.category_var.set(values[2])
        self.date_var.set(values[3])
        self.payment_var.set(values[4])
        self.notes_var.set(values[5])

    def clear_form(self) -> None:
        self.selected_id = None
        self.amount_var.set("")
        self.category_var.set(EXPENSE_CATEGORIES[0])
        self.date_var.set(str(date.today()))
        self.payment_var.set(PAYMENT_METHODS[0])
        self.notes_var.set("")
        self.tree.selection_remove(self.tree.selection())

    # ------------------------------------------------------------------
    def _validated_fields(self):
        amount = validate_amount(self.amount_var.get())
        category = validate_not_empty(self.category_var.get(), "Category")
        expense_date = validate_date(self.date_var.get())
        payment = self.payment_var.get().strip() or "Cash"
        notes = self.notes_var.get().strip()
        return amount, category, expense_date, payment, notes

    def add_expense(self) -> None:
        try:
            amount, category, expense_date, payment, notes = self._validated_fields()
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        self.db.execute(
            """INSERT INTO expenses (user_id, amount, category, date, payment_method, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (self.app.current_user.id, amount, category, expense_date, payment, notes),
        )
        messagebox.showinfo("Success", "Expense added successfully.")
        self.clear_form()
        self.refresh()
        self.app.refresh_dashboard()
        self._check_budget_threshold(expense_date)

    def update_expense(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("No Selection", "Please select an expense row to update.")
            return
        try:
            amount, category, expense_date, payment, notes = self._validated_fields()
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        self.db.execute(
            """UPDATE expenses SET amount = ?, category = ?, date = ?, payment_method = ?, notes = ?
               WHERE id = ? AND user_id = ?""",
            (amount, category, expense_date, payment, notes, self.selected_id, self.app.current_user.id),
        )
        messagebox.showinfo("Success", "Expense updated successfully.")
        self.clear_form()
        self.refresh()
        self.app.refresh_dashboard()
        self._check_budget_threshold(expense_date)

    def delete_expense(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("No Selection", "Please select an expense row to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this expense record?"):
            return

        row = self.db.fetch_one(
            "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
            (self.selected_id, self.app.current_user.id),
        )
        if row is not None:
            self.db.execute(
                "INSERT INTO deleted_items (user_id, item_type, item_data) VALUES (?, 'expense', ?)",
                (self.app.current_user.id, json.dumps(dict(row))),
            )
        self.db.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (self.selected_id, self.app.current_user.id),
        )
        messagebox.showinfo("Deleted", "Expense record deleted. You can undo this from the Settings page.")
        self.clear_form()
        self.refresh()
        self.app.refresh_dashboard()

    # ------------------------------------------------------------------
    def _check_budget_threshold(self, expense_date: str) -> None:
        """Warn the user if their spend for the expense's month crosses 75/90/100%."""
        year, month = expense_date.split("-")[0], expense_date.split("-")[1]
        budget_row = self.db.fetch_one(
            "SELECT amount FROM budget WHERE user_id = ? AND month = ? AND year = ?",
            (self.app.current_user.id, int(month), int(year)),
        )
        if budget_row is None or budget_row["amount"] <= 0:
            return

        spent = self.db.fetch_one(
            """SELECT COALESCE(SUM(amount), 0) AS total FROM expenses
               WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?""",
            (self.app.current_user.id, month, year),
        )["total"]

        budget_amount = budget_row["amount"]
        percent = (spent / budget_amount) * 100
        symbol = self.app.currency_symbol()

        if percent >= 100:
            messagebox.showerror(
                "Budget Exceeded!",
                f"You have exceeded your budget for {year}-{month}!\n"
                f"Spent: {format_currency(spent, symbol)} / {format_currency(budget_amount, symbol)}",
            )
        elif percent >= 90:
            messagebox.showwarning(
                "Budget Warning: 90%",
                f"You have used {percent:.1f}% of your budget for {year}-{month}.",
            )
        elif percent >= 75:
            messagebox.showwarning(
                "Budget Warning: 75%",
                f"You have used {percent:.1f}% of your budget for {year}-{month}.",
            )

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = "SELECT id, amount, category, date, payment_method, notes FROM expenses WHERE user_id = ?"
        params = [self.app.current_user.id]

        search_term = self.search_var.get().strip()
        if search_term:
            query += " AND (notes LIKE ? OR category LIKE ?)"
            params += [f"%{search_term}%", f"%{search_term}%"]

        category = self.filter_category_var.get()
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        month = self.filter_month_var.get().strip()
        if month:
            query += " AND strftime('%m', date) = ?"
            params.append(f"{int(month):02d}")

        year = self.filter_year_var.get().strip()
        if year:
            query += " AND strftime('%Y', date) = ?"
            params.append(year)

        min_amount = self.filter_min_var.get().strip()
        if min_amount:
            query += " AND amount >= ?"
            params.append(float(min_amount))

        max_amount = self.filter_max_var.get().strip()
        if max_amount:
            query += " AND amount <= ?"
            params.append(float(max_amount))

        query += " ORDER BY date DESC, id DESC"

        try:
            rows = self.db.fetch_all(query, tuple(params))
        except (ValueError, Exception) as e:
            messagebox.showerror("Filter Error", f"Invalid filter value: {e}")
            return

        currency_symbol = self.app.currency_symbol()
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    format_currency(row["amount"], currency_symbol),
                    row["category"],
                    row["date"],
                    row["payment_method"] or "",
                    row["notes"] or "",
                ),
            )
