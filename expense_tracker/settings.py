"""
settings.py
-----------
Settings screen: switch between Dark/Light mode, choose a currency,
back up or restore the SQLite database, and undo the most recent
delete (income or expense) via the deleted_items audit table.
"""

import json
import os
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk

from utils import CURRENCIES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SettingsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.db = app.db

        ttk.Label(self, text="Settings", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 15))

        self._build_appearance_section()
        self._build_currency_section()
        self._build_backup_section()
        self._build_undo_section()

    # ------------------------------------------------------------------
    def _build_appearance_section(self) -> None:
        frame = ttk.Labelframe(self, text="Appearance", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(frame, text="Theme:").pack(side="left", padx=(0, 10))
        ttk.Button(
            frame, text="Light Mode", bootstyle="secondary-outline",
            command=lambda: self.app.set_theme("light"),
        ).pack(side="left", padx=4)
        ttk.Button(
            frame, text="Dark Mode", bootstyle="dark",
            command=lambda: self.app.set_theme("dark"),
        ).pack(side="left", padx=4)

    def _build_currency_section(self) -> None:
        frame = ttk.Labelframe(self, text="Currency", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(frame, text="Select Currency:").pack(side="left", padx=(0, 10))
        self.currency_var = ttk.StringVar(value=self.app.get_currency_code())
        combo = ttk.Combobox(
            frame, textvariable=self.currency_var, values=list(CURRENCIES.keys()), state="readonly", width=10
        )
        combo.pack(side="left", padx=4)
        ttk.Button(
            frame, text="Save Currency", bootstyle="primary",
            command=lambda: self.app.set_currency(self.currency_var.get()),
        ).pack(side="left", padx=8)

    def _build_backup_section(self) -> None:
        frame = ttk.Labelframe(self, text="Database Backup / Restore", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        ttk.Button(frame, text="Backup Database", bootstyle="success", command=self.backup_database).pack(
            side="left", padx=4
        )
        ttk.Button(frame, text="Restore Database", bootstyle="warning", command=self.restore_database).pack(
            side="left", padx=4
        )

    def _build_undo_section(self) -> None:
        frame = ttk.Labelframe(self, text="Undo Last Delete", padding=12)
        frame.pack(fill="x", pady=(0, 10))
        ttk.Label(
            frame, text="Restore the most recently deleted income or expense record."
        ).pack(side="left", padx=(0, 10))
        ttk.Button(frame, text="Undo Delete", bootstyle="info", command=self.undo_delete).pack(side="left")

    # ------------------------------------------------------------------
    def backup_database(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".db", filetypes=[("SQLite Database", "*.db")], initialfile="expense_backup.db"
        )
        if not path:
            return
        try:
            self.db.backup(path)
            messagebox.showinfo("Backup Complete", f"Database backed up to:\n{path}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def restore_database(self) -> None:
        if not messagebox.askyesno(
            "Confirm Restore", "This will replace your current data with the backup file. Continue?"
        ):
            return
        path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if not path:
            return
        try:
            self.db.restore(path)
            messagebox.showinfo("Restore Complete", "Database restored successfully. Please restart the app.")
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))

    def undo_delete(self) -> None:
        row = self.db.fetch_one(
            "SELECT * FROM deleted_items WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (self.app.current_user.id,),
        )
        if row is None:
            messagebox.showinfo("Nothing to Undo", "There are no recently deleted records.")
            return

        item_type = row["item_type"]
        data = json.loads(row["item_data"])
        data.pop("id", None)  # let SQLite auto-assign a new id

        if item_type == "income":
            self.db.execute(
                "INSERT INTO income (user_id, amount, source, date, notes) VALUES (?, ?, ?, ?, ?)",
                (data["user_id"], data["amount"], data["source"], data["date"], data.get("notes")),
            )
        elif item_type == "expense":
            self.db.execute(
                """INSERT INTO expenses (user_id, amount, category, date, payment_method, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data["user_id"], data["amount"], data["category"], data["date"],
                    data.get("payment_method"), data.get("notes"),
                ),
            )

        self.db.execute("DELETE FROM deleted_items WHERE id = ?", (row["id"],))
        messagebox.showinfo("Restored", f"The last deleted {item_type} record has been restored.")
        self.app.refresh_dashboard()
