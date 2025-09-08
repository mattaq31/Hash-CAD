# ----------------------------- IMPORTS -------------------------------------
import os, glob, re
import numpy as np
from io import StringIO

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


# ---------------------------- CONSTANTS ------------------------------------
ROW_LABELS = [chr(ord('A') + i) for i in range(16)]  # A..P
COL_LABELS = [str(i) for i in range(1, 25)]          # 1..24


import re
import pandas as pd

def _safe_sheet_name(name: str) -> str:
    """Excel sheet-name safe (<=31 chars, no []:*?/\\)."""
    s = re.sub(r'[\[\]:*?/\\]', '_', str(name))
    return s[:31] if len(s) > 31 else s

def save_low_wells_excel(plates: dict, outpath: str, threshold_ul: float = 20.0):
    """
    Create an Excel file listing all wells below `threshold_ul`.
    - 'Summary' sheet: all plates together
    - One sheet per plate: only that plate's low wells
    Values below the threshold are formatted red.
    """
    low_df = report_wells_below(plates, threshold_ul=threshold_ul)

    with pd.ExcelWriter(outpath, engine="xlsxwriter") as writer:
        # --- Summary sheet ---
        low_df.to_excel(writer, sheet_name="Summary", index=False)
        wb  = writer.book
        ws  = writer.sheets["Summary"]
        red = wb.add_format({"font_color": "red"})

        # Apply conditional format to the 'Current Fluid Volume' column
        n_rows = len(low_df)
        if n_rows > 0:
            # Assuming columns are: Plate (A), Well (B), Current Fluid Volume (C)
            ws.conditional_format(1, 2, n_rows, 2,  # (first_row, first_col, last_row, last_col)
                                  {"type": "cell", "criteria": "<", "value": threshold_ul, "format": red})
            ws.autofilter(0, 0, n_rows, 2)
            for col_idx, width in enumerate([20, 10, 22]):
                ws.set_column(col_idx, col_idx, width)

        # --- Per-plate sheets ---
        for plate_name, obj in plates.items():
            df = obj["df"]
            if "Current Fluid Volume" not in df.columns:
                continue
            mask = df["Current Fluid Volume"] < threshold_ul
            plate_low = (
                df.loc[mask, ["Current Fluid Volume"]]
                  .reset_index()
                  .rename(columns={"Source Well": "Well"})
            )
            sheet = _safe_sheet_name(plate_name)
            plate_low.to_excel(writer, sheet_name=sheet, index=False)
            ws_p = writer.sheets[sheet]

            m_rows = len(plate_low)
            if m_rows > 0:
                # 'Current Fluid Volume' is column C on this sheet as well
                ws_p.conditional_format(1, 2, m_rows, 2,
                                        {"type": "cell", "criteria": "<", "value": threshold_ul, "format": red})
                ws_p.autofilter(0, 0, m_rows, 2)
                for col_idx, width in enumerate([10, 22, 22]):
                    ws_p.set_column(col_idx, col_idx, width)

    print(f"Saved Excel to: {outpath}")


# ----------------------------- PARSING -------------------------------------
def _section_df(lines, tag):
    """Return a DataFrame for a section like [EXCEPTIONS] or [DETAILS]."""
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == tag) + 1
    except StopIteration:
        return pd.DataFrame()
    end = next(
        (j for j in range(start, len(lines))
         if lines[j].strip().startswith("[") and lines[j].strip().endswith("]")),
        len(lines),
    )
    chunk = "".join(lines[start:end]).strip()
    return pd.read_csv(StringIO(chunk)) if chunk else pd.DataFrame()


def read_plate_matrix(path):
    """
    Parse one Labcyte Echo CSV (merge [EXCEPTIONS] then [DETAILS]) and return:
      {"plate_name": str, "matrix": (16x24) ndarray, "df": DataFrame(index='Source Well'), "file": path}
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    df = pd.concat([_section_df(lines, "[EXCEPTIONS]"),
                    _section_df(lines, "[DETAILS]")], ignore_index=True)
    if df.empty:
        raise ValueError(f"{os.path.basename(path)}: no [EXCEPTIONS]/[DETAILS] content")

    needed = {"Source Well", "Current Fluid Volume"}
    if not needed.issubset(df.columns):
        raise ValueError(f"{os.path.basename(path)}: missing required columns {needed}")

    df["Current Fluid Volume"] = pd.to_numeric(df["Current Fluid Volume"], errors="coerce")

    tidy = (
        df[["Source Well", "Current Fluid Volume"]]
        .dropna(subset=["Source Well"])
        .drop_duplicates(subset=["Source Well"], keep="last")  # DETAILS overrides
        .set_index("Source Well")
        .sort_index()
    )

    plate_name = None
    if "Source Plate Name" in df.columns and df["Source Plate Name"].notna().any():
        plate_name = str(df["Source Plate Name"].dropna().iloc[0])

    # build 16x24 matrix (A..P × 1..24)
    matrix = np.full((16, 24), np.nan, dtype=float)
    pat = re.compile(r"^([A-P])(\d{1,2})$")
    for well, vol in tidy["Current Fluid Volume"].items():
        m = pat.match(str(well))
        if not m:
            continue
        r = ord(m.group(1)) - ord("A")
        c = int(m.group(2)) - 1
        if 0 <= r < 16 and 0 <= c < 24:
            matrix[r, c] = vol

    return {"plate_name": plate_name, "matrix": matrix, "df": tidy, "file": path}


def read_plate_folder(folder):
    """
    Return a ONE-LEVEL dict:
      { plate_name: {"matrix": ndarray, "df": DataFrame, "file": path}, ... }
    """
    plates = {}
    for path in glob.glob(os.path.join(folder, "*.csv")):
        try:
            res = read_plate_matrix(path)
        except Exception as e:
            print(f"Skipping {os.path.basename(path)}: {e}")
            continue

        name = res["plate_name"] or os.path.splitext(os.path.basename(path))[0]

        # ensure unique key if duplicates
        key, i = name, 2
        while key in plates:
            key = f"{name} ({i})"
            i += 1

        plates[key] = {"matrix": res["matrix"], "df": res["df"], "file": res["file"]}
    return plates


def combine_all(plates):
    """Return one tidy DataFrame across all plates (MultiIndex: Plate × Well)."""
    rows = []
    for plate_name, obj in plates.items():
        df_long = obj["df"].copy()
        df_long["Plate"] = plate_name
        df_long = df_long.reset_index().rename(columns={"Source Well": "Well"})
        rows.append(df_long)
    if not rows:
        return pd.DataFrame(columns=["Current Fluid Volume"])
    return pd.concat(rows, ignore_index=True).set_index(["Plate", "Well"]).sort_index()


def save_low_wells_pkl(plates, outpath, threshold_ul=20.0):
    """
    Combine all plates into one DataFrame, keep only wells < threshold,
    and save to a pickle file (.pkl).
    """
    all_df = combine_all(plates)
    # filter
    low_df = all_df[all_df["Current Fluid Volume"] < threshold_ul]
    # save
    low_df.to_pickle(outpath)
    print(f"Saved {len(low_df)} low wells to {outpath}")
    return low_df

# ----------------------------- PLOTTING ------------------------------------
def plot_volume_hist(df, bins=20, title="Distribution of Current Fluid Volumes"):
    """Histogram (bar) of Current Fluid Volume counts from a DataFrame with that column."""
    vols = df["Current Fluid Volume"].dropna().to_numpy()
    counts, edges = np.histogram(vols, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    plt.figure(figsize=(8, 5))
    plt.bar(centers, counts, width=np.diff(edges), align="center", edgecolor="black")
    plt.xlabel("Current Fluid Volume (µL)")
    plt.ylabel("Count of Wells")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_plate_heatmap(matrix, title="Current Fluid Volume — plate"):
    """Heatmap for a single plate matrix."""
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(matrix, aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Column (1–24)")
    ax.set_ylabel("Row (A–P)")
    ax.set_xticks(range(24)); ax.set_xticklabels(COL_LABELS)
    ax.set_yticks(range(16)); ax.set_yticklabels(ROW_LABELS)
    fig.colorbar(im, ax=ax, label="Current Fluid Volume (µL)")
    plt.tight_layout()
    plt.show()


def average_plate_matrix(plates):
    """
    Returns (avg_matrix, count_matrix):
      - avg_matrix: NaN-aware mean per well across all plates (16x24)
      - count_matrix: how many plates had a value at that well (16x24, ints)
    """
    mats = [obj["matrix"] for obj in plates.values()]
    if not mats:
        raise ValueError("No plates provided.")
    stack = np.stack(mats, axis=0)
    avg = np.nanmean(stack, axis=0)
    counts = np.sum(~np.isnan(stack), axis=0).astype(int)
    return avg, counts


def plot_average_heatmap(plates, title="Average Current Fluid Volume — All Plates"):
    """Convenience wrapper to compute & plot the average heatmap."""
    avg, _ = average_plate_matrix(plates)
    plot_plate_heatmap(avg, title=title)


def plot_plate_heatmap_with_dots(matrix, threshold_ul=20.0, title="Heatmap"):
    """Heatmap + red circles on cells where value < threshold_ul."""
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(matrix, aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Column (1–24)")
    ax.set_ylabel("Row (A–P)")
    ax.set_xticks(range(24)); ax.set_xticklabels(COL_LABELS)
    ax.set_yticks(range(16)); ax.set_yticklabels(ROW_LABELS)
    fig.colorbar(im, ax=ax, label="Current Fluid Volume (µL)")

    mask = ~np.isnan(matrix) & (matrix < threshold_ul)
    ys, xs = np.where(mask)
    if len(xs) > 0:
        ax.scatter(xs, ys, s=40, facecolors='none', edgecolors='red', linewidths=1.8)

    plt.tight_layout()
    plt.show()


# ------------------------------ REPORTS ------------------------------------
def report_wells_below(plates, threshold_ul=20.0):
    """Return DataFrame: Plate, Well, Current Fluid Volume for wells < threshold."""
    rows = []
    for plate_name, obj in plates.items():
        df = obj["df"]
        if "Current Fluid Volume" not in df.columns:
            continue
        low = df["Current Fluid Volume"] < threshold_ul
        if low.any():
            tmp = df.loc[low, ["Current Fluid Volume"]].copy()
            tmp = tmp.reset_index().rename(columns={"Source Well": "Well"})
            tmp.insert(0, "Plate", plate_name)
            rows.append(tmp)
    if not rows:
        return pd.DataFrame(columns=["Plate", "Well", "Current Fluid Volume"])
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["Plate", "Well"]).reset_index(drop=True)


# ------------------------------- PDF ---------------------------------------
def _plot_heatmap_with_dots(ax, matrix, threshold_ul, title):
    """Internal: used inside the PDF layout."""
    im = ax.imshow(matrix, aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Column (1–24)")
    ax.set_ylabel("Row (A–P)")
    ax.set_xticks(range(24)); ax.set_xticklabels(COL_LABELS)
    ax.set_yticks(range(16)); ax.set_yticklabels(ROW_LABELS)
    mask = ~np.isnan(matrix) & (matrix < threshold_ul)
    ys, xs = np.where(mask)
    if len(xs) > 0:
        ax.scatter(xs, ys, s=40, facecolors='none', edgecolors='red', linewidths=1.8)
    return im


def _plot_volume_hist(ax, vols, bins=20, title=""):
    """Internal: histogram for PDF layout."""
    vols = vols[~np.isnan(vols)]
    if vols.size == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
        return
    counts, edges = np.histogram(vols, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    ax.bar(centers, counts, width=np.diff(edges), align="center", edgecolor="black")
    ax.set_title(title)
    ax.set_xlabel("Current Fluid Volume (µL)")
    ax.set_ylabel("Count of Wells")


def save_plate_report_pdf(plates, outpath, threshold_ul=20.0, bins=20, include_average_page=True):
    """
    Multi-page PDF:
      - For each plate: left = heatmap with red dots (<threshold), right = histogram
      - Optional final page: average heatmap + combined histogram
    """
    with PdfPages(outpath) as pdf:
        # per-plate pages
        for plate_name in sorted(plates.keys()):
            matrix = plates[plate_name]["matrix"]
            vols = plates[plate_name]["df"]["Current Fluid Volume"].to_numpy(dtype=float)

            fig, axes = plt.subplots(1, 2, figsize=(12, 6))

            im = _plot_heatmap_with_dots(
                axes[0], matrix, threshold_ul,
                title=f"{plate_name} — Heatmap (red < {threshold_ul} µL)"
            )
            fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04, label="Current Fluid Volume (µL)")

            _plot_volume_hist(axes[1], vols, bins=bins, title=f"{plate_name} — Volume Distribution")

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

        # average page
        if include_average_page and len(plates) > 1:
            avg_mat, _ = average_plate_matrix(plates)
            all_vols = np.concatenate([
                obj["df"]["Current Fluid Volume"].to_numpy(dtype=float)
                for obj in plates.values()
            ])

            fig, axes = plt.subplots(1, 2, figsize=(12, 6))
            im = _plot_heatmap_with_dots(
                axes[0], avg_mat, threshold_ul,
                title=f"Average Heatmap (red < {threshold_ul} µL)"
            )
            fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04, label="Avg Current Fluid Volume (µL)")

            _plot_volume_hist(axes[1], all_vols, bins=bins, title="All Plates — Volume Distribution")

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

    print(f"Saved PDF to: {outpath}")


# --------------------------- EXAMPLE USAGE ---------------------------------
if __name__ == "__main__":
    folder = r"D:\Wyss_experiments\Echo_survery"   # <- your folder
    plates = read_plate_folder(folder)

    print("Loaded plates:", list(plates.keys()))

    # quick lookup on first plate (if present)
    if plates:
        pname = next(iter(plates))
        df_plate = plates[pname]["df"]
        if "C1" in df_plate.index:
            print("Example C1:", df_plate.loc["C1", "Current Fluid Volume"])

    # combined tidy df
    all_df = combine_all(plates)
    print(all_df.head())

    # optional: quick interactive plots
    # plot_volume_hist(df_plate, bins=15, title=f"{pname} Volumes")
    # plot_plate_heatmap(plates[pname]["matrix"], title=f"Current Fluid Volume — {pname}")
    # plot_average_heatmap(plates, title="Average Current Fluid Volume — All Plates")
    t =25
    # report wells below threshold
    low_df = report_wells_below(plates, threshold_ul=t)
    print("Below threshold wells:\n", low_df)

    # save multi-page PDF
    out_pdf = os.path.join(folder, "plate_volume_report.pdf")
    save_plate_report_pdf(plates, out_pdf, threshold_ul=t, bins=20, include_average_page=True)

    # After you've built `plates = read_plate_folder(folder)`
    save_low_wells_excel(
        plates,
        outpath=os.path.join(r"D:\Wyss_experiments\Echo_survery", "low_wells_report.xlsx"),
        threshold_ul=t
    )

    all_df = combine_all(plates)  # all data
    print(all_df.head())

    low_df = save_low_wells_pkl(
        plates,
        outpath=os.path.join(folder, "low_wells.pkl"),
        threshold_ul=t
    )

    # later: load it back
    df_loaded = pd.read_pickle(os.path.join(folder, "low_wells.pkl"))
    print(df_loaded.head())