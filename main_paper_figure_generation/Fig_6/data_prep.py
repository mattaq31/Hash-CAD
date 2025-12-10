#!/usr/bin/env python3
# Build per-image histograms (bins 1..6) and save as pickle.

from pathlib import Path
import re
import glob
import pandas as pd

# --- EDIT PATHS --------------------------------------------------------------
# require QuPath CSV pick export here
DATA_DIRS = [
    Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/set_A"),
    Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/set_B"),
]
FILES_GLOB = '*pick_data*.csv'
GROUP_REGEX = r'^(V[0-9]+)'
OUT_PKL = Path(r"C:/Users/Flori/Dropbox/CrissCross/Papers/hash_cad/exp2_handle_library_sunflowers/counting/data4paper/Plots/hist_per_image.pkl")
# -----------------------------------------------------------------------------

# collect CSVs
files = []
for folder in DATA_DIRS:
    files.extend(sorted(glob.glob(str(folder / FILES_GLOB))))
if not files:
    print(f'No files matching "{FILES_GLOB}" found in provided folders.')
    raise SystemExit(0)

# helper: image name from CSV filename (covers empty CSVs)
def derive_image_name(csv_filename: str) -> str:
    stem = Path(csv_filename).stem
    return re.sub(r'(_?pick[_-]?data.*)$', '', stem, flags=re.IGNORECASE)

# determine ID col from any header (works even if file is empty)
ID_COL_NAME = None
for fp in files:
    hdr = pd.read_csv(fp, nrows=0)
    cols = hdr.columns.str.strip().tolist()
    if len(cols) >= 2:
        ID_COL_NAME = cols[1]
        break
if ID_COL_NAME is None:
    raise SystemExit("Need at least one CSV with ≥2 columns to detect the ID column.")

# master images table from filenames (captures empty CSVs)
img_rows = []
for fp in files:
    ds  = Path(fp).parent.name
    img = derive_image_name(Path(fp).name)
    m   = re.search(GROUP_REGEX, img, flags=re.IGNORECASE)
    grp = m.group(0).upper() if m else None
    if grp:
        img_rows.append((grp, ds, img, Path(fp).name))

images = (
    pd.DataFrame(img_rows, columns=['Group', 'dataset', 'Image Name', 'source_file'])
      .drop_duplicates()
      .sort_values(['Group', 'dataset', 'Image Name'])
)

# load actual rows (many CSVs may be empty → no rows here, that’s fine)
df_rows = []
for fp in files:
    t = pd.read_csv(fp)
    t.columns = t.columns.str.strip()
    t['dataset']     = Path(fp).parent.name
    t['source_file'] = Path(fp).name
    df_rows.append(t)
df_raw = pd.concat(df_rows, ignore_index=True, sort=False) if df_rows else pd.DataFrame()

# attach canonical (Group, Image Name) via right-merge on (dataset, source_file)
df = (
    images[['Group', 'dataset', 'Image Name', 'source_file']]
      .merge(df_raw, on=['dataset', 'source_file'], how='left', sort=False)
)

# prefer canonical Image Name from filenames if both exist
if 'Image Name_x' in df.columns and 'Image Name_y' in df.columns:
    df['Image Name'] = df['Image Name_x'].fillna(df['Image Name_y'])
    df.drop(columns=['Image Name_x', 'Image Name_y'], inplace=True)

# keep only rows with Group & Image Name
df = df.dropna(subset=['Group', 'Image Name'])

# ---- build per-image hist (bins 1..6, zeros filled) -------------------------
MAX_BIN  = 6
BIN_COLS = pd.Index(range(1, MAX_BIN + 1), name=None)

# counts per (dataset, Group, Image Name, ID)
per_id_counts = (
    df.dropna(subset=[ID_COL_NAME])
      .groupby(['dataset', 'Group', 'Image Name', ID_COL_NAME])
      .size()
      .rename('picks_per_id')
      .reset_index()
)

# hist for images that actually have picks
hist_existing = (
    per_id_counts
      .groupby(['Group', 'dataset', 'Image Name'])['picks_per_id']
      .value_counts()
      .unstack(fill_value=0)
      .reindex(columns=BIN_COLS, fill_value=0)
      .astype(int)
)

# complete table: include images with empty CSVs
hist_per_image = (
    images[['Group', 'dataset', 'Image Name']]
      .merge(hist_existing.reset_index(), on=['Group', 'dataset', 'Image Name'], how='left')
      .fillna(0)
      .set_index(['Group', 'dataset', 'Image Name'])
      .reindex(columns=BIN_COLS)
      .astype(int)
      .sort_index()
)

# save
OUT_PKL.parent.mkdir(parents=True, exist_ok=True)
hist_per_image.to_pickle(OUT_PKL)
print(f"Saved hist_per_image: {OUT_PKL}")
print("Shape:", hist_per_image.shape)
