#!/usr/bin/env python3
"""
Generate a calendar heatmap from WakaTime daily totals.
Requires WAKATIME_API_KEY environment variable.
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
import requests

# ------------------------------
# Configuration
# ------------------------------
USER_ID = "dfcbe794-c409-4097-a53e-aedc2d8b21d6"
API_URL = f"https://wakatime.com/api/v1/users/{USER_ID}/insights/days"
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/143.0.0.0",
}
# Optional: we add Authorization header only if key is present
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    print("❌ WAKATIME_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)

# ------------------------------
# Fetch data from WakaTime
# ------------------------------
def fetch_data():
    """Fetch daily totals for the last year."""
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {API_KEY}"
    try:
        resp = requests.get(API_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # if data.get("status") != "ok":
        #     print("❌ API returned status != ok", file=sys.stderr)
        #     sys.exit(1)
        days = data["data"]["days"]
        # Build dict date -> total seconds
        total_by_date = {}
        for day in days:
            date_str = day["date"]
            total_sec = day.get("total", 0.0)
            total_by_date[date_str] = total_sec
        return total_by_date
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}", file=sys.stderr)
        sys.exit(1)

# ------------------------------
# Build calendar grid
# ------------------------------
def build_grid(total_by_date):
    """Convert date→seconds into a weeks x days grid (Monday first)."""
    # Determine date range (from first to last day in data)
    all_dates = sorted(total_by_date.keys())
    if not all_dates:
        print("❌ No data received", file=sys.stderr)
        sys.exit(1)
    first_date = datetime.strptime(all_dates[0], "%Y-%m-%d")
    last_date = datetime.strptime(all_dates[-1], "%Y-%m-%d")
    # Ensure we cover full weeks: start from Monday before or equal first_date
    start = first_date - timedelta(days=(first_date.weekday() + 7) % 7)  # Monday
    end = last_date
    # Build a matrix: rows = weeks, cols = Mon..Sun
    weeks = []
    current = start
    while current <= end:
        week = []
        for _ in range(7):
            date_str = current.strftime("%Y-%m-%d")
            sec = total_by_date.get(date_str, 0.0)
            hours = sec / 3600.0
            week.append(hours)
            current += timedelta(days=1)
        weeks.append(week)
    # Also store the date grid for annotations
    date_grid = []
    current = start
    while current <= end:
        week_dates = []
        for _ in range(7):
            week_dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        date_grid.append(week_dates)
    # Truncate to full weeks only (remove last incomplete week if it's empty)
    while weeks and all(v == 0 for v in weeks[-1]) and all(d > last_date.strftime("%Y-%m-%d") for d in date_grid[-1]):
        weeks.pop()
        date_grid.pop()
    return np.array(weeks), date_grid, start
# ------------------------------
# Plotting
# ------------------------------
def plot_calendar(data_matrix, date_grid, start_date):
    """Render GitHub-style calendar heatmap."""

    weeks = data_matrix.shape[0]
    days = data_matrix.shape[1]

    fig_w = max(14, weeks * 0.22)
    fig_h = 3.5

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # GitHub-like palette
    colors = [
        "#ebedf0",
        "#c6d4e1",
        "#9fbad0",
        "#6f93b3",
        "#436b8e",
        "#1f1f1f",
    ]

    max_hours = max(data_matrix.flatten()) if data_matrix.size else 1

    def get_color(hours):
        if hours <= 0:
            return colors[0]

        ratio = hours / max_hours

        if ratio < 0.2:
            return colors[1]
        elif ratio < 0.4:
            return colors[2]
        elif ratio < 0.6:
            return colors[3]
        elif ratio < 0.8:
            return colors[4]
        else:
            return colors[5]

    cell_size = 1
    gap = 0.18

    # Draw cells
    for week in range(weeks):
        for day in range(days):

            hours = data_matrix[week, day]

            x = week * (cell_size + gap)
            y = day * (cell_size + gap)

            rect = mpatches.FancyBboxPatch(
                (x, y),
                cell_size,
                cell_size,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                linewidth=0,
                facecolor=get_color(hours),
            )

            ax.add_patch(rect)

    # Day labels
    day_labels = ["Mon", "", "Wed", "", "Fri", "", ""]
    for i, label in enumerate(day_labels):
        if label:
            ax.text(
                -1.5,
                i * (cell_size + gap) + 0.5,
                label,
                ha="right",
                va="center",
                fontsize=10,
                color="#555",
            )

    # Month labels
    prev_month = None

    for week_idx, week_dates in enumerate(date_grid):

        first_day = datetime.strptime(week_dates[0], "%Y-%m-%d")

        if first_day.month != prev_month:
            prev_month = first_day.month

            x = week_idx * (cell_size + gap)

            ax.text(
                x,
                -1.0,
                first_day.strftime("%b"),
                fontsize=10,
                color="#333",
                ha="left",
                va="center",
            )

    # Title
    ax.text(
        0,
        -2.2,
        "ACTIVITY LAST YEAR",
        fontsize=14,
        fontweight="bold",
        color="#333",
        ha="left",
    )

    # Legend
    legend_x = weeks * (cell_size + gap) - 8

    ax.text(
        legend_x - 1.5,
        days * (cell_size + gap) + 0.3,
        "Less",
        fontsize=9,
        color="#555",
        va="center",
    )

    for i, c in enumerate(colors):
        rect = mpatches.FancyBboxPatch(
            (
                legend_x + i * 1.2,
                days * (cell_size + gap),
            ),
            0.9,
            0.9,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=0,
            facecolor=c,
        )
        ax.add_patch(rect)

    ax.text(
        legend_x + len(colors) * 1.2 + 0.3,
        days * (cell_size + gap) + 0.3,
        "More",
        fontsize=9,
        color="#555",
        va="center",
    )

    # Layout
    ax.set_xlim(-2, weeks * (cell_size + gap))
    ax.set_ylim(days * (cell_size + gap) + 2, -3)

    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(
        "coding_calendar.png",
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    print("✅ Saved coding_calendar.png")

# ------------------------------
# Main
# ------------------------------
def main():
    total_by_date = fetch_data()
    data_matrix, date_grid, start_date = build_grid(total_by_date)
    plot_calendar(data_matrix, date_grid, start_date)

if __name__ == "__main__":
    main()
