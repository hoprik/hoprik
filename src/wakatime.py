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
        if data.get("status") != "ok":
            print("❌ API returned status != ok", file=sys.stderr)
            sys.exit(1)
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
    """Create and save the calendar heatmap."""
    weeks, days = data_matrix.shape
    fig, ax = plt.subplots(figsize=(12, weeks * 0.25 + 2))  # dynamic height
    # Use a green colormap, white for zero
    cmap = plt.cm.YlGn
    cmap.set_bad(color='white')
    norm = Normalize(vmin=0, vmax=12)  # up to 12 hours per day (adjust as needed)
    im = ax.imshow(data_matrix, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Hours coded', rotation=270, labelpad=15)

    # Add grid lines
    ax.set_xticks(np.arange(days) - 0.5, minor=True)
    ax.set_yticks(np.arange(weeks) - 0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)

    # Labels for days of week
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    ax.set_xticks(np.arange(days))
    ax.set_xticklabels(day_names)
    ax.tick_params(axis='x', labeltop=True, labelbottom=False)  # put days on top

    # Month labels: iterate over weeks and mark first occurrence of a new month
    month_positions = []
    month_labels = []
    last_month = None
    for i, week_dates in enumerate(date_grid):
        for j, date_str in enumerate(week_dates):
            if date_str == "": continue
            d = datetime.strptime(date_str, "%Y-%m-%d")
            if d.month != last_month:
                last_month = d.month
                month_positions.append((i, j))
                month_labels.append(d.strftime("%b"))
    # Draw month markers above the top
    for (i, j), label in zip(month_positions, month_labels):
        ax.text(j, -0.3, label, ha='center', va='bottom', fontsize=8, weight='bold')
    ax.set_ylim(weeks - 0.5, -0.5)  # invert so week 1 is on top

    # Annotate each cell with hours (if cell width permits)
    for i in range(weeks):
        for j in range(days):
            hours = data_matrix[i, j]
            if hours > 0.01:
                # Decide whether to show text based on cell size
                ax.text(j, i, f"{hours:.1f}", ha='center', va='center', fontsize=6, color='black')

    ax.set_title(f"WakaTime Coding Activity (last year: {start_date.strftime('%b %d, %Y')} – today)")
    ax.set_ylabel("Week number")
    plt.tight_layout()
    plt.savefig("coding_calendar.png", dpi=150, bbox_inches='tight')
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
