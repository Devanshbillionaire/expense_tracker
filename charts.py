"""
charts.py
---------
Builds Matplotlib Figure objects used throughout the app (Dashboard and
Reports screens). Each function returns a `matplotlib.figure.Figure`
that the caller embeds into Tkinter using FigureCanvasTkAgg.

Keeping figure-construction logic here (separate from the widgets that
display them) keeps dashboard.py / reports.py focused on layout only.
"""

from typing import Optional

import matplotlib

matplotlib.use("Agg")  # safe default backend; TkAgg canvas still works for embedding
import matplotlib.pyplot as plt
import pandas as pd

# A calm, professional color palette used consistently across all charts.
PALETTE = [
    "#4C6FFF", "#00BFA6", "#FF6B6B", "#FFB84C", "#8E7DBE",
    "#3AB0FF", "#FF9F68", "#6BCB77", "#C34A36", "#5C6BC0",
]


def _style_axes(ax, dark: bool = False) -> None:
    """Apply a consistent minimal style to a chart axis."""
    bg = "#1E1E2E" if dark else "#FFFFFF"
    fg = "#EAEAEA" if dark else "#333333"
    ax.set_facecolor(bg)
    ax.figure.set_facecolor(bg)
    ax.tick_params(colors=fg, labelsize=8)
    ax.xaxis.label.set_color(fg)
    ax.yaxis.label.set_color(fg)
    ax.title.set_color(fg)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(fg)


def empty_figure(message: str = "No data available", dark: bool = False) -> plt.Figure:
    """Return a placeholder figure when there is nothing to plot."""
    fig = plt.Figure(figsize=(5, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(ax, dark)
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="#999999")
    ax.set_xticks([])
    ax.set_yticks([])
    return fig


def expense_pie_chart(category_totals: dict, dark: bool = False) -> plt.Figure:
    """Pie chart of expenses grouped by category."""
    category_totals = {k: v for k, v in category_totals.items() if v > 0}
    if not category_totals:
        return empty_figure("No expenses to display", dark)

    fig = plt.Figure(figsize=(5, 3.6), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(ax, dark)
    labels = list(category_totals.keys())
    values = list(category_totals.values())
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=PALETTE[: len(labels)],
        textprops={"fontsize": 8, "color": "#EAEAEA" if dark else "#333333"},
        startangle=90,
    )
    ax.set_title("Expenses by Category")
    ax.axis("equal")
    fig.tight_layout()
    return fig


def expense_bar_chart(category_totals: dict, dark: bool = False) -> plt.Figure:
    """Bar chart of expenses grouped by category."""
    category_totals = {k: v for k, v in category_totals.items() if v > 0}
    if not category_totals:
        return empty_figure("No expenses to display", dark)

    fig = plt.Figure(figsize=(5.2, 3.6), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(ax, dark)
    labels = list(category_totals.keys())
    values = list(category_totals.values())
    ax.bar(labels, values, color=PALETTE[: len(labels)])
    ax.set_ylabel("Amount")
    ax.set_title("Expense by Category")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    return fig


def monthly_expense_bar_chart(monthly_totals: dict, dark: bool = False) -> plt.Figure:
    """Bar chart showing total expenses per month (e.g. {'2026-01': 4500, ...})."""
    if not monthly_totals:
        return empty_figure("No expense history yet", dark)

    fig = plt.Figure(figsize=(5.6, 3.6), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(ax, dark)
    months = list(monthly_totals.keys())
    values = list(monthly_totals.values())
    ax.bar(months, values, color="#4C6FFF")
    ax.set_ylabel("Total Expense")
    ax.set_title("Monthly Expense Overview")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def income_vs_expense_line_chart(
    months: list, income_values: list, expense_values: list, dark: bool = False
) -> plt.Figure:
    """Line chart comparing income and expenses across months."""
    if not months:
        return empty_figure("No transactions yet", dark)

    fig = plt.Figure(figsize=(5.6, 3.6), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(ax, dark)
    ax.plot(months, income_values, marker="o", label="Income", color="#00BFA6", linewidth=2)
    ax.plot(months, expense_values, marker="o", label="Expense", color="#FF6B6B", linewidth=2)
    ax.set_title("Income vs Expense")
    ax.set_ylabel("Amount")
    ax.tick_params(axis="x", rotation=45)
    legend = ax.legend(fontsize=8, frameon=False)
    for text in legend.get_texts():
        text.set_color("#EAEAEA" if dark else "#333333")
    fig.tight_layout()
    return fig


def spending_trend_chart(dates: list, amounts: list, dark: bool = False) -> plt.Figure:
    """Line chart of day-by-day spending trend (cumulative or daily)."""
    if not dates:
        return empty_figure("No spending trend data", dark)

    fig = plt.Figure(figsize=(5.6, 3.6), dpi=100)
    ax = fig.add_subplot(111)
    _style_axes(ax, dark)
    ax.plot(dates, amounts, marker=".", color="#8E7DBE", linewidth=2)
    ax.fill_between(range(len(dates)), amounts, color="#8E7DBE", alpha=0.15)
    ax.set_title("Spending Trend")
    ax.set_ylabel("Amount Spent")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def build_category_totals(expense_rows) -> dict:
    """Aggregate a list of expense sqlite3.Row objects into {category: total}."""
    df = pd.DataFrame(
        [dict(row) for row in expense_rows]
    ) if expense_rows else pd.DataFrame(columns=["category", "amount"])
    if df.empty:
        return {}
    grouped = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    return grouped.to_dict()
