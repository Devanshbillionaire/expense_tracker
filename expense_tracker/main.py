"""
main.py
-------
Entry point for the Personal Expense Tracker desktop application.

Responsibilities:
    - Bootstraps the ttkbootstrap-themed Tkinter window
    - Shows Login / Register screens
    - After successful login, builds the main app shell: a sidebar
      navigation bar + a content area that swaps between Dashboard,
      Income, Expense, Budget, Reports and Settings pages.

Run with:  python main.py
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from auth import AuthError, AuthManager, User
from budget import BudgetFrame
from dashboard import DashboardFrame
from database import Database
from expense import ExpenseFrame
from income import IncomeFrame
from reports import ReportsFrame
from settings import SettingsFrame
from utils import CURRENCIES, current_month_year


APP_TITLE = "Personal Expense Tracker"
LIGHT_THEME = "flatly"
DARK_THEME = "darkly"


class LoginFrame(tb.Frame):
    """The login screen, shown first when the app starts."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=30)
        self.app = app

        card = tb.Frame(self, padding=30, bootstyle="light")
        card.place(relx=0.5, rely=0.5, anchor="center")

        tb.Label(card, text=APP_TITLE, font=("Segoe UI", 22, "bold"), bootstyle="inverse-light").pack(
            pady=(0, 20)
        )
        tb.Label(card, text="Login to your account", font=("Segoe UI", 12)).pack(pady=(0, 15))

        tb.Label(card, text="Username").pack(anchor="w")
        self.username_var = tk.StringVar()
        tb.Entry(card, textvariable=self.username_var, width=32).pack(pady=(0, 10))

        tb.Label(card, text="Password").pack(anchor="w")
        self.password_var = tk.StringVar()
        tb.Entry(card, textvariable=self.password_var, show="*", width=32).pack(pady=(0, 20))

        tb.Button(card, text="Login", bootstyle="success", width=28, command=self.login).pack(pady=(0, 8))
        tb.Button(
            card, text="Create a new account", bootstyle="link",
            command=lambda: app.show_frame("register"),
        ).pack()

        # Keyboard shortcut: pressing Enter submits the login form
        self.bind_all("<Return>", lambda e: self.login())

    def login(self) -> None:
        try:
            user = self.app.auth.login(self.username_var.get(), self.password_var.get())
        except AuthError as e:
            messagebox.showerror("Login Failed", str(e))
            return
        self.password_var.set("")
        self.app.on_login_success(user)


class RegisterFrame(tb.Frame):
    """The registration screen for creating a new account."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=30)
        self.app = app

        card = tb.Frame(self, padding=30, bootstyle="light")
        card.place(relx=0.5, rely=0.5, anchor="center")

        tb.Label(card, text="Create Account", font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))

        tb.Label(card, text="Username").pack(anchor="w")
        self.username_var = tk.StringVar()
        tb.Entry(card, textvariable=self.username_var, width=32).pack(pady=(0, 10))

        tb.Label(card, text="Password").pack(anchor="w")
        self.password_var = tk.StringVar()
        tb.Entry(card, textvariable=self.password_var, show="*", width=32).pack(pady=(0, 10))

        tb.Label(card, text="Confirm Password").pack(anchor="w")
        self.confirm_var = tk.StringVar()
        tb.Entry(card, textvariable=self.confirm_var, show="*", width=32).pack(pady=(0, 20))

        tb.Button(card, text="Register", bootstyle="success", width=28, command=self.register).pack(
            pady=(0, 8)
        )
        tb.Button(
            card, text="Back to Login", bootstyle="link", command=lambda: app.show_frame("login")
        ).pack()

    def register(self) -> None:
        try:
            user = self.app.auth.register(
                self.username_var.get(), self.password_var.get(), self.confirm_var.get()
            )
        except AuthError as e:
            messagebox.showerror("Registration Failed", str(e))
            return
        messagebox.showinfo("Success", f"Account '{user.username}' created! Please log in.")
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_var.set("")
        self.app.show_frame("login")


class SidebarButton(tb.Button):
    """A styled navigation button used in the sidebar."""


class MainAppFrame(tb.Frame):
    """The main shell shown after login: sidebar + swappable content pages."""

    NAV_ITEMS = [
        ("dashboard", "🏠 Dashboard"),
        ("income", "💰 Income"),
        ("expense", "💸 Expenses"),
        ("budget", "📊 Budget"),
        ("reports", "📑 Reports"),
        ("settings", "⚙ Settings"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pages = {}
        self.nav_buttons = {}

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

    def _build_sidebar(self) -> None:
        sidebar = tb.Frame(self, bootstyle="dark", width=210)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        tb.Label(
            sidebar, text="Expense\nTracker", font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-dark", padding=(15, 20),
        ).pack(fill="x")

        self.user_label = tb.Label(
            sidebar, text="", bootstyle="inverse-dark", font=("Segoe UI", 10)
        )
        self.user_label.pack(fill="x", padx=15, pady=(0, 10))

        for key, label in self.NAV_ITEMS:
            btn = tb.Button(
                sidebar, text=label, bootstyle="dark", width=20,
                command=lambda k=key: self.app.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = btn

        tb.Button(
            sidebar, text="🚪 Logout", bootstyle="danger", width=20, command=self.app.logout
        ).pack(fill="x", padx=10, pady=(20, 10), side="bottom")

    def _build_content_area(self) -> None:
        self.content = tb.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def build_pages(self) -> None:
        """Instantiate every page frame. Called once, right after login."""
        self.pages = {
            "dashboard": DashboardFrame(self.content, self.app),
            "income": IncomeFrame(self.content, self.app),
            "expense": ExpenseFrame(self.content, self.app),
            "budget": BudgetFrame(self.content, self.app),
            "reports": ReportsFrame(self.content, self.app),
            "settings": SettingsFrame(self.content, self.app),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.user_label.configure(text=f"👤 {self.app.current_user.username}")

    def show_page(self, key: str) -> None:
        for name, page in self.pages.items():
            if name == key:
                page.tkraise()
                if hasattr(page, "refresh"):
                    page.refresh()
        for name, btn in self.nav_buttons.items():
            btn.configure(bootstyle="primary" if name == key else "dark")


class ExpenseTrackerApp:
    """Top-level application controller: owns the DB, auth manager,
    current user/session state, and switches between screens."""

    def __init__(self) -> None:
        self.db = Database()
        self.auth = AuthManager(self.db)
        self.current_user: User | None = None
        self._current_theme = "light"

        self.root = tb.Window(themename=LIGHT_THEME)
        self.root.title(APP_TITLE)
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)

        self.container = tb.Frame(self.root)
        self.container.pack(fill="both", expand=True)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        self.frames = {}
        self.frames["login"] = LoginFrame(self.container, self)
        self.frames["register"] = RegisterFrame(self.container, self)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.main_app_frame: MainAppFrame | None = None

        self._bind_shortcuts()
        self.show_frame("login")

    # ------------------------------------------------------------------
    def _bind_shortcuts(self) -> None:
        """Global keyboard shortcuts for power users."""
        self.root.bind("<Control-d>", lambda e: self.show_page("dashboard"))
        self.root.bind("<Control-i>", lambda e: self.show_page("income"))
        self.root.bind("<Control-e>", lambda e: self.show_page("expense"))
        self.root.bind("<Control-b>", lambda e: self.show_page("budget"))
        self.root.bind("<Control-r>", lambda e: self.show_page("reports"))
        self.root.bind("<Control-q>", lambda e: self.root.quit())

    # ------------------------------------------------------------------
    def show_frame(self, name: str) -> None:
        self.frames[name].tkraise()

    def show_page(self, key: str) -> None:
        if self.main_app_frame is not None:
            self.main_app_frame.show_page(key)

    def on_login_success(self, user: User) -> None:
        self.current_user = user
        self._load_user_settings()

        if self.main_app_frame is not None:
            self.main_app_frame.destroy()
        self.main_app_frame = MainAppFrame(self.container, self)
        self.frames["main"] = self.main_app_frame
        self.main_app_frame.grid(row=0, column=0, sticky="nsew")
        self.main_app_frame.build_pages()
        self.show_frame("main")
        self.show_page("dashboard")
        self._show_monthly_reminder()

    def logout(self) -> None:
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            return
        self.current_user = None
        self.show_frame("login")

    # ------------------------------------------------------------------
    def _load_user_settings(self) -> None:
        row = self.db.fetch_one(
            "SELECT theme, currency FROM settings WHERE user_id = ?", (self.current_user.id,)
        )
        if row is not None:
            self.set_theme(row["theme"], persist=False)
            self._currency_code = row["currency"]
        else:
            self._currency_code = "INR"

    def _show_monthly_reminder(self) -> None:
        """A simple monthly reminder: nudges the user to check/set a budget."""
        month, year = current_month_year()
        budget_row = self.db.fetch_one(
            "SELECT id FROM budget WHERE user_id = ? AND month = ? AND year = ?",
            (self.current_user.id, month, year),
        )
        if budget_row is None:
            messagebox.showinfo(
                "Monthly Reminder",
                "You haven't set a budget for this month yet. "
                "Head to the Budget page to set one and stay on track!",
            )

    # ------------------------------------------------------------------
    # Settings helpers used by settings.py / dashboard.py / etc.
    # ------------------------------------------------------------------
    def set_theme(self, theme: str, persist: bool = True) -> None:
        theme_name = DARK_THEME if theme == "dark" else LIGHT_THEME
        self.root.style.theme_use(theme_name)
        self._current_theme = theme
        if persist and self.current_user is not None:
            self.db.execute(
                "UPDATE settings SET theme = ? WHERE user_id = ?", (theme, self.current_user.id)
            )
        if self.main_app_frame is not None:
            self.refresh_dashboard()

    def is_dark_mode(self) -> bool:
        return self._current_theme == "dark"

    def set_currency(self, code: str) -> None:
        self._currency_code = code
        if self.current_user is not None:
            self.db.execute(
                "UPDATE settings SET currency = ? WHERE user_id = ?", (code, self.current_user.id)
            )
        messagebox.showinfo("Currency Updated", f"Currency set to {code}.")
        self.refresh_dashboard()

    def get_currency_code(self) -> str:
        return getattr(self, "_currency_code", "INR")

    def currency_symbol(self) -> str:
        return CURRENCIES.get(self.get_currency_code(), "\u20b9")

    def refresh_dashboard(self) -> None:
        """Refresh every visible page's data (used after add/edit/delete)."""
        if self.main_app_frame is None:
            return
        for page in self.main_app_frame.pages.values():
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = ExpenseTrackerApp()
    app.run()


if __name__ == "__main__":
    main()
