#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import requests

# =========================================================
# CONFIG
# =========================================================

USER_ID = "dfcbe794-c409-4097-a53e-aedc2d8b21d6"

INSIGHTS_URL = (
    f"https://wakatime.com/api/v1/users/{USER_ID}/insights/days"
)

STATS_URL = (
    f"https://wakatime.com/api/v1/users/{USER_ID}/stats/all_time?timeout=15"
)

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
}

API_KEY = os.environ.get("WAKATIME_API_KEY")

if not API_KEY:
    print("❌ WAKATIME_API_KEY not set", file=sys.stderr)
    sys.exit(1)

# =========================================================
# FETCH
# =========================================================

def auth_headers():
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def fetch_activity():
    resp = requests.get(
        INSIGHTS_URL,
        headers=auth_headers(),
        timeout=30,
    )

    resp.raise_for_status()

    data = resp.json()["data"]["days"]

    totals = {}

    for day in data:
        totals[day["date"]] = day.get("total", 0)

    return totals


def fetch_stats():
    resp = requests.get(
        STATS_URL,
        headers=auth_headers(),
        timeout=30,
    )

    resp.raise_for_status()

    return resp.json()["data"]

# =========================================================
# BUILD GRID
# =========================================================

def build_grid(total_by_date):

    all_dates = sorted(total_by_date.keys())

    first_date = datetime.strptime(all_dates[0], "%Y-%m-%d")
    last_date = datetime.strptime(all_dates[-1], "%Y-%m-%d")

    start = first_date - timedelta(days=first_date.weekday())

    weeks = []

    current = start

    while current <= last_date:

        week = []

        for _ in range(7):

            date_str = current.strftime("%Y-%m-%d")

            sec = total_by_date.get(date_str, 0)

            week.append(sec / 3600)

            current += timedelta(days=1)

        weeks.append(week)

    date_grid = []

    current = start

    while current <= last_date:

        row = []

        for _ in range(7):

            row.append(current.strftime("%Y-%m-%d"))

            current += timedelta(days=1)

        date_grid.append(row)

    return np.array(weeks), date_grid, start

# =========================================================
# HELPERS
# =========================================================

def make_bar(percent, width=18):

    filled = int(width * percent / 100)

    return (
        "█" * filled +
        "░" * (width - filled)
    )


def draw_stats_text(ax, x, y, title, items):

    ax.text(
        x,
        y,
        title,
        fontsize=13,
        fontweight="bold",
        color="#222",
    )

    y += 1.2

    for item in items:

        name = item["name"]

        percent = item["percent"]

        text = item.get("text", "")

        bar = make_bar(percent)

        line = (
            f"{name:<14} "
            f"{text:<10} "
            f"{bar} "
            f"{percent:>5.1f}%"
        )

        ax.text(
            x,
            y,
            line,
            fontsize=9,
            family="monospace",
            color="#444",
        )

        y += 0.8

# =========================================================
# PLOT
# =========================================================

def plot_dashboard(data_matrix, date_grid, start_date, stats):

    weeks = data_matrix.shape[0]
    days = data_matrix.shape[1]

    fig = plt.figure(figsize=(18, 8))

    ax = plt.gca()

    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # -----------------------------------------------------
    # COLORS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    ax.text(
        0,
        -3,
        "WAKATIME DASHBOARD",
        fontsize=22,
        fontweight="bold",
        color="#222",
    )

    ax.text(
        0,
        -1.8,
        f"Total Coding Time: {stats['human_readable_total']}",
        fontsize=11,
        color="#555",
    )

    ax.text(
        0,
        -0.8,
        f"Daily Average: {stats['daily_average']}",
        fontsize=11,
        color="#555",
    )

    # -----------------------------------------------------
    # HEATMAP
    # -----------------------------------------------------

    cell = 1
    gap = 0.18

    for week in range(weeks):

        for day in range(days):

            value = data_matrix[week, day]

            x = week * (cell + gap)

            y = day * (cell + gap)

            rect = mpatches.FancyBboxPatch(
                (x, y),
                cell,
                cell,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                linewidth=0,
                facecolor=get_color(value),
            )

            ax.add_patch(rect)

    # -----------------------------------------------------
    # DAYS
    # -----------------------------------------------------

    labels = ["Mon", "", "Wed", "", "Fri", "", ""]

    for i, label in enumerate(labels):

        if label:

            ax.text(
                -1.3,
                i * (cell + gap) + 0.5,
                label,
                ha="right",
                va="center",
                fontsize=9,
                color="#666",
            )

    # -----------------------------------------------------
    # MONTHS
    # -----------------------------------------------------

    prev_month = None

    for week_idx, week_dates in enumerate(date_grid):

        dt = datetime.strptime(
            week_dates[0],
            "%Y-%m-%d",
        )

        if dt.month != prev_month:

            prev_month = dt.month

            ax.text(
                week_idx * (cell + gap),
                -0.6,
                dt.strftime("%b"),
                fontsize=9,
                color="#444",
            )

    # -----------------------------------------------------
    # LEGEND
    # -----------------------------------------------------

    legend_x = weeks * (cell + gap) - 7

    ax.text(
        legend_x - 1.5,
        8.7,
        "Less",
        fontsize=8,
        color="#555",
    )

    for i, color in enumerate(colors):

        rect = mpatches.FancyBboxPatch(
            (legend_x + i * 1.1, 8.3),
            0.8,
            0.8,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=0,
            facecolor=color,
        )

        ax.add_patch(rect)

    ax.text(
        legend_x + len(colors) * 1.1 + 0.2,
        8.7,
        "More",
        fontsize=8,
        color="#555",
    )

    # -----------------------------------------------------
    # SIDE STATS
    # -----------------------------------------------------

    stats_x = weeks * (cell + gap) + 4

    draw_stats_text(
        ax,
        stats_x,
        0,
        "Languages",
        stats["languages"][:6],
    )

    draw_stats_text(
        ax,
        stats_x,
        8,
        "Editors",
        stats["editors"][:4],
    )

    draw_stats_text(
        ax,
        stats_x,
        14,
        "Operating Systems",
        stats["operating_systems"][:4],
    )

    draw_stats_text(
        ax,
        stats_x,
        20,
        "Categories",
        stats["categories"][:4],
    )

    # -----------------------------------------------------
    # FINALIZE
    # -----------------------------------------------------

    ax.set_xlim(-2, stats_x + 28)

    ax.set_ylim(28, -4)

    ax.axis("off")

    plt.tight_layout()

    plt.savefig(
        "coding_dashboard.png",
        dpi=220,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    print("✅ Saved coding_dashboard.png")

# =========================================================
# MAIN
# =========================================================

def main():

    totals = fetch_activity()

    stats = fetch_stats()

    matrix, date_grid, start = build_grid(totals)

    plot_dashboard(
        matrix,
        date_grid,
        start,
        stats,
    )


if __name__ == "__main__":
    main()
