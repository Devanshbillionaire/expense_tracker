# Personal Expense Tracker

A complete, professional desktop **Expense Tracker** built with **Python 3.12**, **Tkinter + ttkbootstrap** (modern UI), **SQLite** (storage), **Matplotlib** (charts) and **Pandas** (reporting/exports).

---

## Features

- **User Authentication** — Register / Login / Logout with PBKDF2-SHA256 password hashing (per-user random salt, no plaintext passwords ever stored).
- **Dashboard** — Total income, total expense, current balance, this-month spend, recent transactions table, expense pie chart, expense bar chart.
- **Income Management** — Add / Edit / Delete / Search income (Amount, Source, Date, Notes).
- **Expense Management** — Add / Edit / Delete / Search / Filter expenses (Amount, Category, Date, Payment Method, Notes) across 10 built-in categories.
- **Budget Management** — Set a monthly budget, live progress bar, remaining-budget display, automatic warnings at **75% / 90% / 100%** usage.
- **Reports** — Daily / Weekly / Monthly / Yearly reports with export to **CSV**, **Excel (.xlsx)** and **PDF**.
- **Charts** — Expense-by-category pie & bar charts, monthly expense trend, income vs. expense line chart, spending trend graph.
- **Search & Filter** — Filter expenses by date, month, year, category and amount range.
- **Settings** — Light/Dark theme, currency selector (INR/USD/EUR/GBP), database backup & restore.
- **Extra touches** — Auto-save (every change commits to SQLite immediately), undo-last-delete, sortable transaction tables, keyboard shortcuts (Ctrl+D/I/E/B/R for pages, Ctrl+Q to quit), monthly budget reminder on login.

---

## Project Structure

```
expense_tracker/
│
├── main.py            # App entry point, login/register screens, sidebar shell
├── database.py         # SQLite schema + Database helper class
├── auth.py             # Registration / login / password hashing
├── dashboard.py        # Dashboard page (cards, recent transactions, charts)
├── income.py           # Income CRUD + search
├── expense.py           # Expense CRUD + search/filter + budget alerts
├── budget.py           # Monthly budget + progress bar
├── reports.py          # Daily/Weekly/Monthly/Yearly reports + CSV/Excel/PDF export
├── charts.py           # Matplotlib figure builders (pie/bar/line charts)
├── settings.py          # Theme, currency, backup/restore, undo-delete
├── utils.py            # Shared validation & formatting helpers
│
├── database/
│   └── expense.db      # Created automatically on first run
│
├── assets/
│   ├── icons/
│   └── images/
│
├── exports/             # Default folder suggested when exporting reports
│
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Prerequisites

- Python 3.12+ (Python 3.10+ should also work)
- **Tkinter** — this ships with most official Python installers (Windows/macOS). On Linux, install it via your package manager, e.g.:

  ```bash
  sudo apt-get install python3-tk
  ```

### 2. Clone / copy the project

Place the `expense_tracker/` folder anywhere on your machine.

### 3. Create a virtual environment (recommended)

```bash
cd expense_tracker
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## How to Run

```bash
python main.py
```

1. Register a new account on first launch.
2. Log in.
3. Use the left sidebar to move between **Dashboard**, **Income**, **Expenses**, **Budget**, **Reports** and **Settings**.

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+D | Go to Dashboard |
| Ctrl+I | Go to Income |
| Ctrl+E | Go to Expenses |
| Ctrl+B | Go to Budget |
| Ctrl+R | Go to Reports |
| Ctrl+Q | Quit application |
| Enter (on login screen) | Submit login |

---

## Database

SQLite database is created automatically at `database/expense.db` on first run, with the following tables (foreign keys enforced via `PRAGMA foreign_keys = ON`):

- `users` — id, username, password_hash, salt, created_at
- `income` — id, user_id (FK), amount, source, date, notes, created_at
- `expenses` — id, user_id (FK), amount, category, date, payment_method, notes, created_at
- `budget` — id, user_id (FK), month, year, amount
- `settings` — id, user_id (FK), theme, currency
- `deleted_items` — id, user_id (FK), item_type, item_data (JSON), deleted_at — powers the "Undo Delete" feature

Use **Settings → Backup Database** to copy the `.db` file elsewhere, and **Restore Database** to bring an old backup back.

---

## Screenshots

> _Add screenshots here after running the app locally, e.g.:_
>
> - `assets/images/dashboard.png`
> - `assets/images/expenses.png`
> - `assets/images/reports.png`

---

## Future Improvements

- Multi-currency support with live exchange-rate conversion
- Cloud sync / multi-device support
- Recurring transactions (auto-add rent, subscriptions, salary)
- Mobile companion app
- Export dashboard as a shareable PDF snapshot
- Role-based multi-user households with shared budgets
- Receipt photo attachments (OCR auto-fill of amount/category)

---

## Tech Stack

| Purpose | Library |
|---|---|
| GUI | Tkinter + ttkbootstrap |
| Database | SQLite (`sqlite3`, standard library) |
| Charts | Matplotlib |
| Reports / data wrangling | Pandas |
| Excel export | openpyxl |
| PDF export | ReportLab |

---

## License

This project was generated as a personal learning/portfolio project and is free to use, modify and extend.
