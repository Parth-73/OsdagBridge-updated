"""Render report charts with Agg without changing the desktop backend."""

from textwrap import fill

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from .report_utils import _finite_number
from .styles import (
    CHART_DPI, CHART_FAILURE, CHART_GRID, CHART_LABEL_SIZE, CHART_PASS,
    CHART_TEXT, CHART_WIDTH, OSDAG_GREEN, UR_LIMIT,
)


def _save_bar_chart(values, path, title, xlabel, *, limit=None, axis_max=None):
    labels, numbers = zip(*values)
    colors = OSDAG_GREEN if limit is None else [
        CHART_PASS if number <= limit else CHART_FAILURE for number in numbers
    ]
    vertical = limit is not None
    size = (CHART_WIDTH, 4.4 if vertical else max(2.1, 1.4 + 0.34 * len(values)))
    figure = Figure(figsize=size, constrained_layout=True)
    FigureCanvasAgg(figure)
    try:
        ax = figure.subplots()
        if vertical:
            bars = ax.bar(labels, numbers, color=colors, width=0.65)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels([fill(label, width=18) for label in labels],
                               rotation=35, ha="right", rotation_mode="anchor")
            ax.set_ylim(0, axis_max)
            ax.axhline(limit, color=CHART_FAILURE, linestyle="--", linewidth=1.4,
                       label=f"UR = {limit:.1f}", zorder=3)
            ax.legend(loc="upper right", frameon=False, fontsize=CHART_LABEL_SIZE - 1)
            ax.set(ylabel=xlabel)
            ax.yaxis.grid(color=CHART_GRID)
        else:
            bars = ax.barh(labels, numbers, color=colors, height=0.65)
            ax.invert_yaxis()
            ax.set_xlim(0, max(numbers) * 1.2 or 1)
            ax.set(xlabel=xlabel)
            ax.xaxis.grid(color=CHART_GRID)
        value_labels = [f"{value:.2f}" if vertical else f"{value:g}" for value in numbers]
        ax.bar_label(bars, labels=value_labels, padding=4, color=CHART_TEXT,
                     fontsize=CHART_LABEL_SIZE - 1)
        ax.set(title=title)
        ax.title.set_color(CHART_TEXT)
        ax.xaxis.label.set_color(CHART_TEXT)
        ax.yaxis.label.set_color(CHART_TEXT)
        ax.tick_params(labelsize=CHART_LABEL_SIZE, colors=CHART_TEXT)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        figure.savefig(path, dpi=CHART_DPI)
    finally:
        # This Figure is unmanaged by pyplot and has no GUI window to close.
        figure.clear()


def _available_values(rows):
    values = []
    for label, raw in rows:
        value = _finite_number(raw)
        if value is not None and value >= 0:
            values.append((label, value))
    return values


def generate_utilization_charts(rows, image_dir):
    """Return relative paths to the charts, with at most eight checks per page."""
    values = _available_values(rows)
    if not values:
        return []
    axis_max = 1.2 * max(UR_LIMIT, max(value for _, value in values))
    paths = []
    for start in range(0, len(values), 8):
        name = f"utilization_{len(paths) + 1}.png"
        _save_bar_chart(values[start:start + 8], image_dir / name,
                        "Design check utilization", "Utilization ratio",
                        limit=UR_LIMIT, axis_max=axis_max)
        paths.append(f"images/{name}")
    return paths


def generate_quantity_chart(rows, image_dir, name, title, xlabel):
    values = _available_values(rows)
    if not values:
        return None
    _save_bar_chart(values, image_dir / name, title, xlabel)
    return f"images/{name}"
