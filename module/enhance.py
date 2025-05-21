import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import statistics
import warnings
import datetime
import openai

# MAIN ENHANCE FUNCTION

def enhance_plot(
    ax,
    interactive=False,
    user_profile=None,
    auto_legend=True,
    auto_label=True,
    openai_api_key=None,
    config=None,
):
    """
    Enhances a Matplotlib Axes object by applying user-centered improvements:
    readability, accessibility, interactivity, and structured alt-text.

    Parameters:
        ax : matplotlib.axes.Axes
            The plot to enhance.
        interactive : bool
            Enable hover tooltips.
        user_profile : str
            Preset profile (e.g., 'colorblind', 'visually_impaired').
        auto_legend : bool
            Automatically create legend if needed.
        auto_label : bool
            Automatically label bars/lines.
        openai_api_key : str
            API key for richer alt-text (optional).
        config : dict
            Configuration flags for granular control.
    """

    # 1. Default configuration
    default_config = {
        "color_palette": [
            "#377eb8",  # Blue (colorblind-safe)
            "#4daf4a",  # Green
            "#984ea3",  # Purple
            "#ff7f00",  # Orange
        ],
        "font_size": 12,  # Base font size for all text
        "visually_impaired_font": 16,  # Larger font for visually impaired
        "misleading_yaxis_threshold": 0,
        "auto_rotate_labels": True,
        "auto_sort_bars": True,
        "minimal_mode": False,
        "show_alt_text_on_figure": False,
        "enable_tooltip": True,
        "enable_legend_toggle": True,
        "enhancement_level": "auto",
    }

    # Merge user config
    if config is None:
        config = default_config.copy()
    else:
        for key, val in default_config.items():
            config.setdefault(key, val)

    # 2. Determine chart type for targeted enhancements
    chart_type = _detect_chart_type(ax)

    # 3. Apply user profile settings (colors, font sizes)
    _apply_user_profile(ax, user_profile, config)

    # 4. Chart-type-specific enhancements
    if chart_type == "bar":
        if config.get("auto_sort_bars", False):
            _sort_bar_chart(ax)
        _adjust_bar_spacing(ax)
        if auto_label:
            _auto_label(ax, config)
            # Hide only y-axis tick labels and ticks when bar labels are shown, keep axis spine and label
            ax.tick_params(axis='y', which='both', labelleft=False, left=False)
        if config.get("minimal_mode", False):
            # Minimal mode: hide y-axis ticks but keep spine and label
            ax.tick_params(axis='y', which='both', labelleft=False, left=False)

    elif chart_type == "pie":
        # Warn if too many slices
        _warn_pie_overload(ax)
        # Reorder slices to interleave large/small if many small adjacent
        _reorder_pie_slices(ax)
        # Apply colorblind-safe palette for pie if needed
        # (handled by palette routine if user_profile=='colorblind')
        if user_profile == "colorblind":
            _apply_colorblind_palette(ax, config)
        # Push small-slice labels outward
        _optimize_pie_labels(ax)

    elif chart_type == "line":
        lines = ax.get_lines()
        if len(lines) == 1:
            line = lines[0]
            lbl = line.get_label()
            if not lbl or lbl.startswith("_"):
                # use the y-axis label as the series name
                line.set_label(ax.get_ylabel() or "Sales")
        if auto_label:
            _label_line_ends(ax, config)
        _warn_line_overplot(ax)                   
        _annotate_peaks_troughs(ax, config)
        if not config["minimal_mode"]:
            _add_grid(ax)         


    elif chart_type == "scatter":
        # 1) Warn & mitigate overplot
        _warn_scatter_overplot(ax)
        _adjust_scatter_alpha(ax)
        # 2) Annotate extremes
        _annotate_scatter_extremes(ax, config)
        # 3) Add light grid
        _add_grid(ax)

    
    # 5. Auto-assign axis labels, misleading checks and label rotation
    _auto_assign_axis_labels(ax, chart_type)
    _check_misleading(ax, config)
    _auto_label_rotation(ax, config)

    # 6. Legend handling Legend handling
    if auto_legend:
        _auto_legend(ax)
    if config.get("enable_legend_toggle", False):
        _enable_legend_toggle(ax)

    # 7. Interactivity (tooltips)
    if interactive and config.get("enable_tooltip", False):
        _enable_interactive(ax)

    # 8. Alt-text generation and optional in-figure display
    alt_text = generate_alt_text(ax, openai_api_key=openai_api_key, config=config)
    ax.alt_text = alt_text
    # Print alt-text summary to terminal for screen readers or logs
    print(f"[VizHelper] Alt-text: {alt_text}")
    if config.get("show_alt_text_on_figure", False):
        _show_alt_text_on_figure(ax, alt_text, config)

    # 9. Final layout adjustment
    ax.figure.tight_layout()



# ==================== Helper Functions ====================

# Chart type detection
from matplotlib.collections import PathCollection

def _detect_chart_type(ax):
    """
    Identify chart type based on Axes children:
    - pie: Wedge patches
    - bar: Rectangle patches (width > 0)
    - scatter: PathCollection
    - line: Line2D
    """
    # Pie chart detection
    if any(isinstance(p, mpl.patches.Wedge) for p in ax.patches):
        return "pie"
    # Bar chart detection
    if any(isinstance(p, mpl.patches.Rectangle) and p.get_width() > 0 for p in ax.patches):
        return "bar"
    # Scatter detection
    if any(isinstance(c, PathCollection) for c in ax.collections):
        return "scatter"
    # Line detection
    if any(isinstance(l, mpl.lines.Line2D) for l in ax.lines):
        return "line"
    return "unknown"


# User profile adjustments

def _apply_user_profile(ax, user_profile, config):
    """
    Adjust settings based on user profile:
    - visually_impaired: increase base font size
    """
    # Font size adaptation
    base_fs = config.get("font_size", 12)
    if user_profile == "visually_impaired":
        base_fs = config.get("visually_impaired_font", 16)
    plt.rcParams.update({"font.size": base_fs})

    if user_profile == "colorblind":
        _apply_colorblind_palette(ax, config)


# Color accessibility

def _apply_colorblind_palette(ax, config):
    """
    Replace low-contrast/default colors with high-contrast ones for all chart types.
    """
    import matplotlib.colors as mcolors

    palette = config.get("color_palette", ["#377eb8"])  # fallback to blue
    high_contrast = palette[0]
    chart_type = _detect_chart_type(ax)

    LOW_CONTRAST_COLORS = {
        "#e41a1c", "red",
        "#4daf4a", "green",
        "#999999", "gray", "grey",
        "#8a6d8f", "#a65628", "#f781bf"
    }

    def is_low_contrast(color):
        try:
            hex_color = mcolors.to_hex(color).lower()
            return hex_color in LOW_CONTRAST_COLORS or color in LOW_CONTRAST_COLORS
        except:
            return False

    if chart_type == "bar":
        for bar in ax.patches:
            if isinstance(bar, mpl.patches.Rectangle) and bar.get_width() > 0:
                if is_low_contrast(bar.get_facecolor()):
                    bar.set_facecolor(high_contrast)

    elif chart_type == "line":
        for line in ax.get_lines():
            if is_low_contrast(line.get_color()):
                line.set_color(high_contrast)

    elif chart_type == "pie":
        for patch in ax.patches:
            if isinstance(patch, mpl.patches.Wedge):
                if is_low_contrast(patch.get_facecolor()):
                    patch.set_facecolor(high_contrast)

    elif chart_type == "scatter":
        for coll in ax.collections:
            if hasattr(coll, 'get_facecolor') and is_low_contrast(coll.get_facecolor()):
                coll.set_facecolor(high_contrast)

    print("[VizHelper] Applied colorblind-friendly palette.")




def _sort_bar_chart(ax):
    """
    Sort bar chart in ascending order by height when more than 6 bars,
    preserving axis labels, title, and original bar colors.
    Also log count, minimum, maximum, average, and range.
    """
    bars = [p for p in ax.patches if isinstance(p, mpl.patches.Rectangle) and p.get_width() > 0]
    n_bars = len(bars)
    if n_bars <= 6:
        return
    # Preserve existing labels and title
    xlabel = ax.get_xlabel()
    ylabel = ax.get_ylabel()
    title = ax.get_title()
    # Extract labels, values, and colors
    labels = [tick.get_text() for tick in ax.get_xticklabels() if tick.get_text()]
    values = [bar.get_height() for bar in bars]
    colors = [bar.get_facecolor() for bar in bars]
    # Sort ascending by value
    sorted_data = sorted(zip(values, labels, colors), key=lambda x: x[0])
    vals, labs, cols = zip(*sorted_data)
    # Clear and redraw each bar to preserve original colors
    ax.clear()
    for lab, val, col in zip(labs, vals, cols):
        ax.bar(lab, val, color=col)
    # Restore axis labels and title
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    # Compute and log detailed stats
    minimum = vals[0]
    maximum = vals[-1]
    mean_val = statistics.mean(vals)
    data_range = maximum - minimum
    print(f"[VizHelper] Sorted {n_bars} bars; min={minimum:.1f}, max={maximum:.1f}, avg={mean_val:.1f}, range={data_range:.1f}.")



def _adjust_bar_spacing(ax):
    """
    Dynamically adjust bar widths and spacing based on count:
      - <=3 bars: width=0.5
      - 4-6 bars: width=0.7
      - 7-10 bars: width=0.6
      - >10 bars: width=0.4
    """
    bars = [p for p in ax.patches if isinstance(p, mpl.patches.Rectangle) and p.get_width() > 0]
    n = len(bars)
    if n == 0:
        return
    if n <= 3:
        width = 0.5
    elif n <= 6:
        width = 0.7
    elif n <= 10:
        width = 0.6
    else:
        width = 0.4
    # Center each bar with new width
    for bar in bars:
        center = bar.get_x() + bar.get_width() / 2
        bar.set_width(width)
        bar.set_x(center - width / 2)
    print(f"[VizHelper] Adjusted bar widths to {width} for {n} bars.")




def _optimize_pie_labels(ax, threshold=0.05, offset=1.2):
    """
    Push small-slice labels outward to reduce overlap.
    """
    wedges = [p for p in ax.patches if isinstance(p, mpl.patches.Wedge)]
    texts = ax.texts
    total = sum((w.theta2 - w.theta1) for w in wedges)
    for w, t in zip(wedges, texts):
        frac = (w.theta2 - w.theta1) / 360.0
        if frac < threshold:
            x, y = t.get_position()
            t.set_position((x * offset, y * offset))
    print("[VizHelper] Optimized pie slice labels.")




# Warn pie chart overload

def _warn_pie_overload(ax, threshold=10):
    """
    Warn in terminal if pie chart has more slices than threshold and recommend alternative.
    """
    wedges = [p for p in ax.patches if isinstance(p, mpl.patches.Wedge)]
    n = len(wedges)
    if n > threshold:
        print(f"[VizHelper Warning] Pie chart has {n} slices; consider using a bar chart or donut chart for better readability.")



# Reorder pie slices to interleave large and small

def _reorder_pie_slices(ax):
    """
    Reorders pie slices by interleaving largest and smallest slices to reduce label overlap,
    while preserving the original title.
    """
    # 1) Capture existing title
    old_title = ax.get_title()
    # 2) Gather wedges, labels, colors
    wedges = [p for p in ax.patches if isinstance(p, mpl.patches.Wedge)]
    labels = [t.get_text() for t in ax.texts if '%' not in t.get_text()]
    startangle = wedges[0].theta1 if wedges else 0
    fractions = [(w.theta2 - w.theta1) / 360.0 for w in wedges]
    colors    = [w.get_facecolor() for w in wedges]

    # 3) Sort and interleave large/small
    data = sorted(zip(fractions, labels, colors), key=lambda x: x[0])
    left, right = 0, len(data) - 1
    interleaved = []
    while left <= right:
        interleaved.append(data[right])
        right -= 1
        if left <= right:
            interleaved.append(data[left])
            left += 1

    # 4) Clear & redraw
    ax.clear()
    if interleaved:
        fracs, labs, cols = zip(*interleaved)
        ax.pie(
            fracs,
            labels=labs,
            autopct='%1.1f%%',
            startangle=startangle,
            colors=cols
        )
    ax.axis('equal')

    # 5) Restore title
    ax.set_title(old_title)

    print("[VizHelper] Reordered pie slices to interleave large and small segments.")



# Label line ends

def _label_line_ends(ax, config):
    """
    Add labels at the end of each line series, but only if it's explicitly named.
    """
    fs = config.get("font_size", 12)
    for line in ax.get_lines():
        label = line.get_label()
        if not label or label.startswith("_"):
            continue

        xdata, ydata = line.get_xdata(), line.get_ydata()
        if len(xdata):
            ax.text(
                xdata[-1],
                ydata[-1],
                label,
                ha="left",
                va="bottom",
                fontsize=fs,
            )
    print("[VizHelper] Labeled line endpoints.")



def _warn_line_overplot(ax, threshold=200):             
    total = sum(len(l.get_xdata()) for l in ax.lines)
    if total > threshold:
        print(f"[VizHelper Warning] Line chart has {total} points; consider smoothing or aggregation.")



def _annotate_peaks_troughs(ax, config):                
    fs = config["font_size"]
    for line in ax.lines:
        x,y = line.get_xdata(), line.get_ydata()
        if len(y)==0: continue
        imax = int(np.argmax(y)); imin = int(np.argmin(y))
        ax.annotate(f"max {y[imax]:.1f}",
                    xy=(x[imax], y[imax]),
                    xytext=(0,5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=fs)
        ax.annotate(f"min {y[imin]:.1f}",
                    xy=(x[imin], y[imin]),
                    xytext=(0,-10),
                    textcoords="offset points",
                    ha='center', va='top', fontsize=fs)
    print("[VizHelper] Annotated peaks and troughs.")



def _add_grid(ax):                                     
    ax.grid(True)
    print("[VizHelper] Grid enabled for line chart/scatter plot.")



# Warn scatter overplotting

def _warn_scatter_overplot(ax, threshold=500):
    """
    Suggest hexbin/density if too many points.
    """
    for coll in ax.collections:
        if isinstance(coll, PathCollection):
            n = len(coll.get_offsets())
            if n > threshold:
                print(f"[VizHelper] Warning: {n} points - consider hexbin.")



# Interactivity via mplcursors

def _enable_interactive(ax):
    """
    Enable hover tooltips with custom info, suppressing the Wedge‐pick warning.
    """
    # Ignore mplcursors’ “Pick support for Wedge is missing” warning
    warnings.filterwarnings(
        "ignore",
        message="Pick support for Wedge is missing.*",
        category=UserWarning,
    )
    try:
        import mplcursors
        cursor = mplcursors.cursor(ax, hover=True)
        @cursor.connect("add")
        def on_add(sel):
            artist = sel.artist
            if isinstance(artist, mpl.patches.Rectangle):
                sel.annotation.set_text(f"Value: {artist.get_height():.2f}")
            elif isinstance(artist, mpl.lines.Line2D):
                x, y = sel.target
                sel.annotation.set_text(f"x={x:.2f}\ny={y:.2f}")
            else:
                x, y = sel.target
                sel.annotation.set_text(f"x={x:.2f}\ny={y:.2f}")
        print("[VizHelper] Tooltips enabled.")
    except ImportError:
        warnings.warn("Install mplcursors for tooltips.")



# Clickable legend toggle

def _enable_legend_toggle(ax):
    """
    Toggle visibility by clicking legend entries.
    """
    legend = ax.get_legend()
    if not legend:
        return
    lines = ax.get_lines()
    leglines = legend.get_lines()
    mapping = dict(zip(leglines, lines))
    for leg in leglines:
        leg.set_picker(True)
    def on_pick(event):
        leg = event.artist
        orig = mapping.get(leg)
        if orig:
            vis = not orig.get_visible()
            orig.set_visible(vis)
            leg.set_alpha(1.0 if vis else 0.2)
            ax.figure.canvas.draw()
    ax.figure.canvas.mpl_connect('pick_event', on_pick)
    print("[VizHelper] Legend toggle enabled.")



# Display alt text on figure

def _show_alt_text_on_figure(ax, alt_text, config):
    """
    Render alt-text as a caption below the plot.
    """
    fs = config.get("font_size", 14)
    fig = ax.figure
    fig.text(0.5, 0.01, alt_text, ha='center', va='bottom',
             wrap=True, fontsize=fs * 0.9)
    print("[VizHelper] Displayed alt-text on figure.")



# Misleading visualization checks

def _check_misleading(ax, config):
    y_min, _ = ax.get_ylim()
    if y_min > config.get("misleading_yaxis_threshold", 0):
        print("[VizHelper Warning] Y-axis does not start at zero.")
    wedges = [p for p in ax.patches if isinstance(p, mpl.patches.Wedge)]
    if wedges:
        total_angle = sum(w.theta2 - w.theta1 for w in wedges)
        if abs(total_angle - 360) > 5:
            print(f"[VizHelper Warning] Pie angles sum to {total_angle:.1f}°.")



# Auto-rotate labels

def _auto_label_rotation(ax, config):
    if not config.get("auto_rotate_labels", False):
        return
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    n = len(labels)
    rot = 90 if n > 10 else 45 if n > 5 else 0
    ax.tick_params(axis='x', labelrotation=rot)
    if rot:
        print(f"[VizHelper] Rotated x-labels {rot}°.")



# Auto-legend creation

def _auto_legend(ax):
    """
    Create a legend if auto_legend is True.
    """
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend()
        print("[VizHelper] Legend created automatically.")



# Auto-label bars and lines

def _auto_label(ax, config):
    bars = [p for p in ax.patches if isinstance(p, mpl.patches.Rectangle) and p.get_width() > 0]
    fs = config.get("font_size", 14)
    for bar in bars:
        x = bar.get_x() + bar.get_width()/2
        y = bar.get_height()
        ax.text(x, y, f"{y:.1f}", ha='center', va='bottom', fontsize=fs)
    for line in ax.get_lines():
        xdata, ydata = line.get_xdata(), line.get_ydata()
        if len(xdata):
            ax.text(xdata[-1], ydata[-1], line.get_label(), ha='left', va='bottom', fontsize=fs)
    if bars or ax.get_lines():
        print("[VizHelper] Data labels added.")



# Alt-text generation (heuristic)

def _generate_heuristic_alt_text(ax, config):
    import matplotlib as m
    # PIE CHART
    wedges = [w for w in ax.patches if isinstance(w, m.patches.Wedge)]
    if wedges:
        # get labels (skip the autopct texts)
        labels = [t.get_text() for t in ax.texts if t.get_text() and "%" not in t.get_text()]
        # compute fractions
        fracs = [(w.theta2 - w.theta1) / 360.0 for w in wedges]
        # find smallest & largest
        max_i = fracs.index(max(fracs))
        min_i = fracs.index(min(fracs))
        biggest, smallest = labels[max_i], labels[min_i]
        # convert to percentages
        pct_big = fracs[max_i] * 100
        pct_small = fracs[min_i] * 100
        # build the description
        return (
            f"Pie chart has the following slices: {', '.join(labels)}. "
            f"The largest slice is '{biggest}' ({pct_big:.1f}%), "
            f"and the smallest slice is '{smallest}' ({pct_small:.1f}%)."
        )
    # Bar chart
    bars = [p for p in ax.patches if isinstance(p, mpl.patches.Rectangle) and p.get_width()>0]
    if bars:
        labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
        values = [bar.get_height() for bar in bars]
        if labels:
            return f"Bar chart with categories {', '.join(labels)}"
        return "Bar chart with multiple values."
    
    # Line chart
    lines = ax.lines
    if lines:
        n_series = len(lines)
        pts = sum(len(l.get_xdata()) for l in lines)
        trends = {"increasing" if l.get_ydata()[-1]>l.get_ydata()[0] else "decreasing" for l in lines if len(l.get_ydata())>1}
        all_x = np.concatenate([l.get_xdata() for l in lines])
        all_y = np.concatenate([l.get_ydata() for l in lines])
        imax,imin = int(np.argmax(all_y)), int(np.argmin(all_y))
        return (
            f"Line chart with {n_series} series and {pts} points, trend(s): {', '.join(trends)}. "
            f"Overall max {all_y[imax]:.1f} at x={all_x[imax]}, min {all_y[imin]:.1f} at x={all_x[imin]}."
        )
    
    # SCATTER
    for coll in ax.collections:
        if isinstance(coll, PathCollection):
            pts = coll.get_offsets()
            n = len(pts)
            if n == 0:
                continue
            xs, ys = pts[:,0], pts[:,1]
            xmin, xmax = xs.min(), xs.max()
            ymin, ymax = ys.min(), ys.max()
            return (
                f"Scatter plot with {n} points. "
                f"X ranges from {xmin:.1f} to {xmax:.1f}, "
                f"Y ranges from {ymin:.1f} to {ymax:.1f}."
            )

    return "A Matplotlib chart."




# Auto-assign missing axis labels

def _auto_assign_axis_labels(ax, chart_type):
    """
    Automatically set x and y axis labels when the user has not provided them.
    - pie: do nothing
    - bar: Category / Value
    - line/scatter: if title contains "Foo vs Bar", use that; else Date/X and series label/Value
    """
    title = ax.get_title() or ""

    # 1) pies get no axes
    if chart_type == "pie":
        return

    # 2) if title contains "foo vs bar", split and use
    if " vs " in title.lower():
        left, right = title.split(" vs ", 1)
        ax.set_xlabel(left.strip())
        ax.set_ylabel(right.strip())
        return

    # 3) bar charts
    if chart_type == "bar":
        if not ax.get_xlabel():
            ax.set_xlabel("Category")
        if not ax.get_ylabel():
            ax.set_ylabel("Value")
        return

    # 4) lines & scatter fallback:

    # 4a) X-axis
    if not ax.get_xlabel():
        x_vals = []
        if ax.get_lines():
            x_vals = ax.get_lines()[0].get_xdata()
        elif ax.collections:
            coll = next((c for c in ax.collections 
                         if isinstance(c, PathCollection)), None)
            if coll is not None and len(coll.get_offsets()):
                x_vals = coll.get_offsets()[:,0]
        if len(x_vals) and isinstance(x_vals[0], (datetime.datetime, np.datetime64)):
            ax.set_xlabel("Date")
        else:
            ax.set_xlabel("X")

    # 4b) Y-axis
    if not ax.get_ylabel():
        labels = [
            line.get_label()
            for line in ax.get_lines()
            if line.get_label() and not line.get_label().startswith("_")
        ]
        ax.set_ylabel(labels[0] if labels else "Value")



def _adjust_scatter_alpha(ax, low_alpha=0.6, threshold=200):
    """
    Reduce marker alpha if too many points, to reveal density.
    """
    for coll in ax.collections:
        if isinstance(coll, PathCollection):
            n = len(coll.get_offsets())
            if n > threshold:
                coll.set_alpha(low_alpha)
                print(f"[VizHelper] Reduced scatter alpha to {low_alpha} for {n} points.")



def _annotate_scatter_extremes(ax, config):
    """
    Find and annotate the highest and lowest Y-value points.
    """
    fs = config.get("font_size", 12)
    for coll in ax.collections:
        if isinstance(coll, PathCollection):
            pts = coll.get_offsets()
            if pts.size == 0:
                continue
            xs, ys = pts[:,0], pts[:,1]
            idx_max = int(np.argmax(ys))
            idx_min = int(np.argmin(ys))
            x_max, y_max = xs[idx_max], ys[idx_max]
            x_min, y_min = xs[idx_min], ys[idx_min]
            ax.annotate(f"max {y_max:.1f}",
                        xy=(x_max, y_max),
                        xytext=(0,5),
                        textcoords="offset points",
                        ha="center", va="bottom",
                        fontsize=fs)
            ax.annotate(f"min {y_min:.1f}",
                        xy=(x_min, y_min),
                        xytext=(0,-10),
                        textcoords="offset points",
                        ha="center", va="top",
                        fontsize=fs)
    print("[VizHelper] Annotated scatter extremes.")


    
# Full alt-text interface

def generate_alt_text(ax, openai_api_key=None, config=None):
    """
    Alt-text interface.  If the user gave an OpenAI key,
    call the AI generator; otherwise use the heuristic.
    """
    if openai_api_key:
        return _generate_ai_alt_text(ax, openai_api_key, config)
    return _generate_heuristic_alt_text(ax, config)



def _generate_ai_alt_text(ax, api_key, config):
    """
    Generate alt-text using OpenAI’s ChatCompletion API.
    Falls back to heuristic on any failure.
    """

    openai.api_key = api_key

    # helper to grab first real line-label
    def _first_series_label():
        for line in ax.get_lines():
            lbl = line.get_label()
            if lbl and not lbl.startswith("_"):
                return lbl
        return None

    chart_type = _detect_chart_type(ax)

    if chart_type == "pie":
        wedges = [w for w in ax.patches if isinstance(w, mpl.patches.Wedge)]
        labels = [t.get_text() for t in ax.texts if t.get_text() and "%" not in t.get_text()]
        fracs  = [(w.theta2 - w.theta1) / 360.0 for w in wedges]
        prompt = (
            f"This is a pie chart with {len(labels)} slices: {', '.join(labels)}. "
            f"Their percentages are {', '.join(f'{100*f:.1f}%' for f in fracs)}. "
            "Write a concise alt-text describing the chart."
        )

    elif chart_type == "bar":
        bars   = [b for b in ax.patches if isinstance(b, mpl.patches.Rectangle) and b.get_width() > 0]
        labels = [tick.get_text() for tick in ax.get_xticklabels() if tick.get_text()]
        vals   = [b.get_height() for b in bars]
        prompt = (
            f"This is a bar chart with categories {', '.join(labels)} and values "
            f"{', '.join(f'{v:.1f}' for v in vals)}. Write a concise alt-text describing the chart."
        )

    elif chart_type == "line":
        lines = ax.get_lines()
        series = []
        for line in lines:
            lbl = line.get_label()
            if not lbl or lbl.startswith("_"):
                lbl = _first_series_label() or "series"
            y = line.get_ydata()
            trend = "increasing" if len(y)>1 and y[-1]>y[0] else "decreasing" if len(y)>1 else "flat"
            series.append(f"{lbl} ({trend})")
        prompt = (
            f"This is a line chart with {len(lines)} series: {', '.join(series)}. "
            "Write a concise alt-text describing the trends."
        )

    elif chart_type == "scatter":
        pts = []
        for coll in ax.collections:
            if isinstance(coll, mpl.collections.PathCollection):
                pts = coll.get_offsets()
                break
        if len(pts):
            xs, ys = pts[:,0], pts[:,1]
            prompt = (
                f"This is a scatter plot with {len(pts)} points. "
                f"x ranges from {xs.min():.1f} to {xs.max():.1f}, "
                f"y ranges from {ys.min():.1f} to {ys.max():.1f}. "
                "Write a concise alt-text describing the distribution."
            )
        else:
            prompt = "This is a scatter plot. Write a concise alt-text."

    else:
        prompt = "Write a concise alt-text description for this chart."

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[VizHelper] OpenAI API call failed: {e}")
        return _generate_heuristic_alt_text(ax, config)


