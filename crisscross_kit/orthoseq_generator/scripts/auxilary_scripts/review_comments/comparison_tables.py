"""Consistent manuscript comparison boxes that extend the canvas without rescaling histogram panels."""

from matplotlib.patches import Rectangle


def add_comparison_boxes(fig, panels, boxes):
    """Append (title, column headings, rows, widths) boxes below the existing, physically unchanged panels.

    Dimensions are in PDF points, so row spacing and borders stay consistent at manuscript text width.
    Call after finalizing panel positions and figure-level method headings.
    """
    row_pt, title_pt, gap_pt, bottom_pt = 11, 14, 8, 8
    heights = [title_pt + row_pt * (len(rows) + bool(headings)) for _, headings, rows, _ in boxes]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    old_height = fig.get_figheight() * 72
    panel_bottom = min(ax.get_tightbbox(renderer).y0 for ax in panels) * 72 / fig.dpi
    # Measure labels as well as axes, leaving a real gap below the lowest histogram label.
    top_distance = old_height - panel_bottom + 10
    new_height = max(old_height, top_distance + sum(heights) + gap_pt * (len(boxes) - 1) + bottom_pt)
    positions = [ax.get_position().frozen() for ax in panels]
    text_positions = [(text, text.get_position()) for text in fig.texts]
    fig.set_size_inches(fig.get_figwidth(), new_height / 72, forward=True)
    for ax, position in zip(panels, positions):
        ax.set_position([position.x0, 1 - (1 - position.y0) * old_height / new_height,
                         position.width, position.height * old_height / new_height])
    for text, (x, y) in text_positions:
        text.set_position((x, 1 - (1 - y) * old_height / new_height))

    top = new_height - top_distance
    for (title, headings, rows, widths), height in zip(boxes, heights):
        ax = fig.add_axes([0.08, (top - height) / new_height, 0.905, height / new_height])
        ax.set_axis_off()
        body_height = height - title_pt
        ax.add_patch(Rectangle((0, body_height / height), 1, title_pt / height,
                               transform=ax.transAxes, facecolor="0.95", edgecolor="none"))
        ax.text(0.02, (height - title_pt / 2) / height, title, transform=ax.transAxes,
                ha="left", va="center", fontsize=7, fontweight="bold")
        table = ax.table(cellText=rows, colLabels=headings, colWidths=widths,
                         cellLoc="left", colLoc="left", bbox=[0, 0, 1, body_height / height])
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        for (row, col), cell in table.get_celld().items():
            cell.visible_edges = ("R" if col < len(widths) - 1 else "")
            if row < len(rows) + bool(headings) - 1:
                cell.visible_edges += "B"
            cell.set_edgecolor("0.65")
            cell.set_linewidth(0.3)
            cell.set_facecolor("white")
            cell.PAD = 0.02 / widths[col]
            if headings and row == 0:
                cell.get_text().set_fontweight("bold")
        ax.plot([0, 1], [body_height / height] * 2, transform=ax.transAxes, color="black", linewidth=0.5)
        ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False,
                               edgecolor="black", linewidth=0.5, clip_on=False))
        top -= height + gap_pt
