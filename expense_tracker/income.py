"""
income.py
---------
Income management screen: add, edit, delete and search income records.

Fields: Amount, Source, Date, Notes
"""

import json
import tkinter as tk
from datetime import date
from tkinter import messagebox
import ttkbootstrap as ttk

from utils import ValidationError, validate_amount, validate_date, validate_not_empty, format_currency


class IncomeFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.db = app.db
        self.selected_id = None

        self._build_header()
        self._build_form()
        self._build_search_bar()
        self._build_table()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        ttk.Label(self, text="Income Management", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", pady=(0, 15)
        )

    def _build_form(self) -> None:
        form = ttk.Labelframe(self, text="Add / Edit Income", padding=12)
        form.pack(fill="x", pady=(0, 10))
        for i in range(4):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Amount").grid(row=0, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_var).grid(row=1, column=0, sticky="ew", padx=4)

        ttk.Label(form, text="Source").grid(row=0, column=1, sticky="w")
        self.source_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.source_var).grid(row=1, column=1, sticky="ew", padx=4)

        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w")
        self.date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(form, textvariable=self.date_var).grid(row=1, column=2, sticky="ew", padx=4)

        ttk.Label(form, text="Notes").grid(row=0, column=3, sticky="w")
        self.notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.notes_var).grid(row=1, column=3, sticky="ew", padx=4)

        btn_row = ttk.Frame(form)
        btn_row.grid(row=2, column=0, columnspan=4, pady=(10, 0), sticky="w")
        ttk.Button(btn_row, text="Add Income", bootstyle="success", command=self.add_income).pack(
            side="left", padx=4
        )
        ttk.Button(
            btn_row, text="Update Selected", bootstyle="info", command=self.update_income
        ).pack(side="left", padx=4)
        ttk.Button(
            btn_row, text="Delete Selected", bootstyle="danger", command=self.delete_income
        ).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Form", bootstyle="secondary-outline", command=self.clear_form).pack(
            side="left", padx=4
        )

    def _build_search_bar(self) -> None:
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text="Search (source/notes):").pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh())
        ttk.Button(search_frame, text="Clear", command=lambda: (self.search_var.set(""), self.refresh())).pack(
            side="left"
        )

    def _build_table(self) -> None:
        columns = ("id", "amount", "source", "date", "notes")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, label, width in zip(
            columns, ("ID", "Amount", "Source", "Date", "Notes"), (40, 100, 150, 100, 250)
        ):
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
        self.source_var.set(values[2])
        self.date_var.set(values[3])
        self.notes_var.set(values[4])

    def clear_form(self) -> None:
        self.selected_id = None
        self.amount_var.set("")
        self.source_var.set("")
        self.date_var.set(str(date.today()))
        self.notes_var.set("")
        self.tree.selection_remove(self.tree.selection())

    # ------------------------------------------------------------------
    def _validated_fields(self):
        amount = validate_amount(self.amount_var.get())
        source = validate_not_empty(self.source_var.get(), "Source")
        income_date = validate_date(self.date_var.get())
        notes = self.notes_var.get().strip()
        return amount, source, income_date, notes

    def add_income(self) -> None:
        try:
            amount, source, income_date, notes = self._validated_fields()
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        self.db.execute(
            "INSERT INTO income (user_id, amount, source, date, notes) VALUES (?, ?, ?, ?, ?)",
            (self.app.current_user.id, amount, source, income_date, notes),
        )
        messagebox.showinfo("Success", "Income added successfully.")
        self.clear_form()
        self.refresh()
        self.app.refresh_dashboard()

    def update_income(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("No Selection", "Please select an income row to update.")
            return
        try:
            amount, source, income_date, notes = self._validated_fields()
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        self.db.execute(
            "UPDATE income SET amount = ?, source = ?, date = ?, notes = ? WHERE id = ? AND user_id = ?",
            (amount, source, income_date, notes, self.selected_id, self.app.current_user.id),
        )
        messagebox.showinfo("Success", "Income updated successfully.")
        self.clear_form()
        self.refresh()
        self.app.refresh_dashboard()

    def delete_income(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("No Selection", "Please select an income row to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this income record?"):
            return

        row = self.db.fetch_one(
            "SELECT * FROM income WHERE id = ? AND user_id = ?",
            (self.selected_id, self.app.current_user.id),
        )
        if row is not None:
            # Save to deleted_items so it can be restored via "Undo Delete"
            self.db.execute(
                "INSERT INTO deleted_items (user_id, item_type, item_data) VALUES (?, 'income', ?)",
                (self.app.current_user.id, json.dumps(dict(row))),
            )
        self.db.execute(
            "DELETE FROM income WHERE id = ? AND user_id = ?",
            (self.selected_id, self.app.current_user.id),
        )
        messagebox.showinfo("Deleted", "Income record deleted. You can undo this from the Settings page.")
        self.clear_form()
        self.refresh()
        self.app.refresh_dashboard()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = "SELECT id, amount, source, date, notes FROM income WHERE user_id = ?"
        params = [self.app.current_user.id]
        search_term = self.search_var.get().strip()
        if search_term:
            query += " AND (source LIKE ? OR notes LIKE ?)"
            params += [f"%{search_term}%", f"%{search_term}%"]
        query += " ORDER BY date DESC, id DESC"

        rows = self.db.fetch_all(query, tuple(params))
        currency_symbol = self.app.currency_symbol()
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    format_currency(row["amount"], currency_symbol),
                    row["source"],
                    row["date"],
                    row["notes"] or "",
                ),
            )
