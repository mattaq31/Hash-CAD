from pathlib import Path
from io import StringIO
import pandas as pd
from crisscross.plate_mapping import get_cutting_edge_plates

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os


ROWS_96 = list("ABCDEFGH")
COLS_96 = list(range(1, 13))
POS_96  = [f"{r}{c}" for r in ROWS_96 for c in COLS_96]  # A1..H12


WELL_RX = r"^[A-Pa-p](?:[1-9]|1\d|2[0-4])$"  # A–P, 1–24

LETTERS = list("ABCDEFGHIJKLMNOP")
NUMBERS = range(1, 25)

def read_echo_folder(folder):
    rows = []
    for f in Path(folder).glob("*.csv"):
        txt = Path(f).read_text(encoding="utf-8", errors="ignore")
        for tag in ("[EXCEPTIONS]", "[DETAILS]"):
            if tag not in txt:
                continue
            # take this section up to the next section header if present
            block = txt.split(tag, 1)[1].split("\n[", 1)[0]
            df = pd.read_csv(StringIO(block))

            # keep only real wells; this also drops the "Instrument ..." footer rows
            df = df[df["Source Well"].astype(str).str.match(WELL_RX)]

            fluid_vol_column = 'Current Fluid Volume' if 'Current Fluid Volume' in df.columns else 'Survey Fluid Volume'
            df = df[["Source Plate Name", "Source Well", fluid_vol_column]].copy()

            df["Plate"]  = df.pop("Source Plate Name")
            df["Letter"] = df["Source Well"].str[0].str.upper()
            df["Number"] = df["Source Well"].str[1:].astype(int)
            df["Volumendata"] = df.pop(fluid_vol_column)

            rows.append(df[["Plate", "Letter", "Number", "Volumendata"]])

    if not rows:
        mi = pd.MultiIndex.from_arrays([[], [], []], names=("Plate","Letter","Number"))
        return pd.DataFrame({"Volumendata": []}, index=mi)

    out = pd.concat(rows, ignore_index=True)


    out = out.set_index(["Plate","Letter","Number"]).sort_index()
    all_plates = out.index.get_level_values("Plate").unique()
    full_idx = pd.MultiIndex.from_product([all_plates, LETTERS, NUMBERS],
                                          names=["Plate","Letter","Number"])
    return out.reindex(full_idx)

def _expand_wells_str(s):
    s = str(s).strip()
    if s.startswith("{") and s.endswith("}"):
        return [w.strip() for w in s[1:-1].split(";") if w.strip()]
    return [s]

def collect_sequences_all(main_plates):
    rows = []
    for H in main_plates:
        for key in H.wells:                            # (category, slat_pos, slat_side, cargo_id)
            full_name = H.get_plate_name(*key)         # e.g. 'P3651_MA_H5_handles_S1C' or 'sw_src009'
            seq       = H.get_sequence(*key)

            for well in _expand_wells_str(H.get_well(*key)):   # 'A2' or many like '{M13;N13;...}'
                rows.append({
                    "FullPlate": full_name,
                    "Well": well,
                    "Sequence": seq,
                    "Seqkey": key,  # NEW
                })
    return pd.DataFrame(rows, columns=["FullPlate", "Well", "Sequence", "Seqkey"])

def seq_lookup_df(main_plates):
    df_seq = collect_sequences_all(main_plates)
    df_seq["Plate"]  = df_seq["FullPlate"].str.extract(r"^([A-Za-z0-9]+_[A-Za-z0-9]+)")
    df_seq["Letter"] = df_seq["Well"].str[0].str.upper()
    df_seq["Number"] = df_seq["Well"].str.extract(r"(\d+)$").astype(int)

    df_seq["SeqLabel"] = df_seq["Seqkey"].map(key_to_human)
    return df_seq.set_index(["Plate", "Letter", "Number"])[["Sequence", "Seqkey", "SeqLabel"]]

def _title_keep_underscores(s: str) -> str:
    """ASSEMBLY_HANDLE -> Assembly_Handle; FLAT -> Flat; 'h5' -> H5."""
    s = str(s)
    parts = s.replace("-", "_").split("_")
    parts = [p.capitalize() if p else p for p in parts]
    return "_".join(parts)

def key_to_human(key) -> str:
    """
    (ASSEMBLY_HANDLE, 1, 5, 10) -> 'Type: Assembly_Handle; Position: 1; Helix: 5; Sequence: 10'
    (FLAT, 4, 2, BLANK)        -> 'Type: Flat; Position: 4; Helix: 2; Sequence: Blank'
    """

    category, slat_position, slat_side, cargo_id = key


    cat = _title_keep_underscores(category)
    # numbers/strings are fine either way; just stringify without losing ints
    pos   = slat_position
    helix = slat_side
    seqid = _title_keep_underscores(cargo_id)

    return f"Type: {cat}; Position: {pos}; Helix: {helix}; Sequence: {seqid}"

def _plot_heatmap_with_dots(ax, mat, threshold_ul, plate):
    """
    Square-cell heatmap with full gray grid, bold 4x4 super-grid,
    red circles at wells below threshold,
    mirrored tick labels (top + right),
    summary line of how many wells are below threshold,
    and fixed color scale 0–100 µL for comparability.
    """
    im = ax.imshow(
        mat,
        aspect="equal",
        interpolation="nearest",
        origin="upper",
        cmap="viridis",
        vmin=0, vmax=100      # fixed scale
    )
    ax.set_title(f"{plate} — Heatmap (red < {threshold_ul} µL)", fontsize=12)
    ax.set_xlabel("Column (1–24)", fontsize=10)
    ax.set_ylabel("Row (A–P)", fontsize=10)

    # Main ticks
    ax.set_xticks(range(24))
    ax.set_xticklabels(NUMBERS, fontsize=8, rotation=90)
    ax.set_yticks(range(16))
    ax.set_yticklabels(LETTERS, fontsize=8)

    # Mirror ticks on top and right
    ax.tick_params(top=True, labeltop=True, bottom=True, labelbottom=True)
    ax.tick_params(left=True, labelleft=True, right=True, labelright=True)

    # Thin gray full grid
    for c in range(25):
        ax.axvline(c - 0.5, color="gray", linewidth=0.85)
    for r in range(17):
        ax.axhline(r - 0.5, color="gray", linewidth=0.85)

    # Bold black  super-grid
    for c in range(0, 25, 6):
        ax.axvline(c - 0.5, color="black", linewidth=1.6)
    for r in range(0, 17, 4):
        ax.axhline(r - 0.5, color="black", linewidth=1.6)

    # Red circles at wells < threshold
    mask = ~np.isnan(mat) & (mat < threshold_ul)
    ys, xs = np.where(mask)
    n_below = len(xs)
    if n_below:
        ax.scatter(xs, ys, s=60, marker="o", facecolors="none",
                   edgecolors="red", linewidths=2)

    # Add summary line below heatmap
    ax.text(
        0.5, -0.15,
        f"{n_below} wells below {threshold_ul} µL",
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=9, color="red" if n_below else "black"
    )

    return im


def _plot_hist(ax, vols, threshold_ul, plate, bins=20):
    vols = vols[~np.isnan(vols)]
    counts, edges = np.histogram(vols, bins=bins, range=(0, 100))  # fixed 0–100 range
    centers = (edges[:-1] + edges[1:]) / 2

    ax.bar(centers, counts, width=np.diff(edges),
           align="center", edgecolor="black")

    # threshold line
    ax.axvline(threshold_ul, linestyle="--", color="red", linewidth=1.5)
    ax.text(threshold_ul, ax.get_ylim()[1]*0.95,
            f"{threshold_ul} µL",
            ha="left", va="top", color="red", fontsize=9, rotation=90)

    ax.set_xlim(0, 100)   # force same range as heatmap
    ax.set_xlabel("Current Fluid Volume (µL)")
    ax.set_ylabel("Count of Wells")
    ax.set_title(f"{plate} — Volume Distribution")

def save_plate_report_pdf_from_df(df, outpath, threshold_ul=20.0, bins=20):
    """
    df: MultiIndex (Plate, Letter, Number) with column 'Volumendata'
    Creates a page per plate: left = square heatmap + 4x4 super-grid; right = histogram.
    """
    plates = df.index.get_level_values("Plate").unique().tolist()
    with PdfPages(outpath) as pdf:
        for plate in plates:
            s = df.xs(plate, level="Plate")["Volumendata"]
            wide = (
                s.unstack("Number")
                 .reindex(index=LETTERS, columns=NUMBERS)
            )
            mat = wide.values.astype(float)
            vols = wide.to_numpy().ravel().astype(float)

            fig, axes = plt.subplots(1, 2, figsize=(12, 6))
            im = _plot_heatmap_with_dots(axes[0], mat, threshold_ul, plate)
            fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04,
                         label="Current Fluid Volume (µL)")
            _plot_hist(axes[1], vols, threshold_ul, plate, bins=bins)

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

    print(f"Saved PDF to: {outpath}")

def wells_below_threshold(df, threshold_ul=20.0):
    """
    Return a filtered DataFrame of wells below the threshold.
    Keeps Plate, Letter, Number, Volumendata, Sequence.
    """
    return df[df["Volumendata"] < threshold_ul].copy()


def make_refill_excel_simple(low_df, outpath):
    """
    Write one 96-well refill sheet per Plate.
    low_df must have MultiIndex (Plate, Letter, Number) and columns Volumendata, Sequence.
    """
    # build well labels like "C18"
    low_df = low_df.copy()
    low_df["Well"] = low_df.index.get_level_values("Letter") + low_df.index.get_level_values("Number").astype(str)

    with pd.ExcelWriter(outpath, engine="xlsxwriter") as writer:
        for plate_name, plate_df in low_df.groupby(level="Plate"):

            if len(plate_df) > 96:
                plate_type = '384'
            else:
                plate_type = '96'
            
            # put Letter/Number back into columns (instead of index)
            plate_df = plate_df.reset_index()

            # assign destination positions on the 96-well refill plate
            if plate_type == '96':
                plate_df["WellPosition"] = POS_96[:len(plate_df)]
            else:
                # or simply do 1:1 with a 384-well plate
                plate_df['WellPosition'] = plate_df['Letter'] + plate_df['Number'].astype(str)

            # label like "Refill C17"
            plate_df["Name"] ="Refill " + plate_df["Letter"] + plate_df["Number"].astype(str)

            # note for traceability
            plate_df["Note"] = "Refill " + plate_name + "; Well " + plate_df["Letter"] + plate_df[
                "Number"].astype(str) + "\t \n" + plate_df["SeqLabel"]

            # write only the required columns
            plate_df[["WellPosition", "Name", "Sequence", "Note"]] \
                .to_excel(writer, sheet_name="Refill "+plate_name, index=False)

    print(f"Saved refill sheets → {outpath}")

# --- example usage with your existing volume df ---
if __name__ == "__main__":
    # your volume df (already built earlier)
    folder= r"D:\Wyss_experiments\Echo_survery"
    main_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Shared Experiment Files/echo_assembly_handle_plate_survey_oct_2025/'
    survey_folder = os.path.join(main_folder, 'echo_surveys_05_09_2025')

    df_vol = read_echo_folder(survey_folder)

    main_plates = get_cutting_edge_plates(100)
    test = collect_sequences_all(main_plates)
    seq_s = seq_lookup_df(main_plates)

    df = df_vol.join(seq_s)  # adds a new 'Sequence' column (left join)

    # we manually removed an addition 2ul from the below wells after the survey report was generated
    additional_2ul_transfers = pd.DataFrame([
        ["P3649_MA", "A1"],
        ["P3649_MA", "A3"],
        ["P3649_MA", "A5"],
        ["P3649_MA", "E1"],
        ["P3649_MA", "G1"],
        ["P3649_MA", "I1"],
        ["P3649_MA", "N16"],
        ["P3649_MA", "N23"],
        ["P3649_MA", "P1"],
        ["P3649_MA", "P18"],
        ["P3649_MA", "P22"],
        ["P3649_MA", "P24"],
        ["P3649_MA", "P3"],
        ["P3650_MA", "A17"],
        ["P3650_MA", "J24"],
        ["P3650_MA", "N24"],
        ["P3650_MA", "P22"],
        ["P3650_MA", "P23"],
        ["P3650_MA", "P24"],
        ["P3651_MA", "A22"],
        ["P3651_MA", "A23"],
        ["P3651_MA", "C24"],
        ["P3651_MA", "F1"],
        ["P3651_MA", "F24"],
        ["P3651_MA", "I1"],
        ["P3651_MA", "I24"],
        ["P3651_MA", "J21"],
        ["P3651_MA", "J24"],
        ["P3651_MA", "K1"],
        ["P3652_MA", "A21"],
        ["P3652_MA", "A24"],
        ["P3652_MA", "C1"],
        ["P3652_MA", "G1"],
        ["P3652_MA", "N24"],
        ["P3652_MA", "O14"],
        ["P3652_MA", "O4"],
        ["P3652_MA", "P20"],
        ["P3652_MA", "P23"],
        ["P3654_MA", "A24"],
        ["P3655_MA", "P2"],
        ["P3655_MA", "P24"],
        ["P3656_MA", "H1"],
        ["P3656_MA", "I1"],
        ["P3656_MA", "J1"],
        ["P3656_MA", "M1"],
        ["P3656_MA", "N1"],
        ["P3657_MA", "A21"],
        ["P3657_MA", "A6"],
        ["P3657_MA", "G24"],
        ["P3659_MA", "L1"],
    ], columns=["Plate", "Well"])


    for plate, well in additional_2ul_transfers.itertuples(index=False):
        letter = well[0]
        number = int(well[1:])
        idx = (plate, letter, number)
        if idx in df.index:
            df.loc[idx, "Volumendata"] = df.loc[idx, "Volumendata"] - 2.0
        else:
            print(f"Warning: {idx} not found in df index; cannot add 2 µL")

    # Set the threshold
    t = 28  # 10ul echo dead volume + 8ul per working stock (40ul/200uM) *2 + 2ul buffer

    save_plate_report_pdf_from_df(
        df,
        outpath=os.path.join(main_folder, "plate_volume_report.pdf"),
        threshold_ul=t)

    low_df = wells_below_threshold(df, threshold_ul=t)
    print('Total low volume cells:', len(low_df))
    make_refill_excel_simple(low_df, os.path.join(main_folder, "refill.xlsx"))
