import os
from collections import defaultdict

input_star_file = '/Users/matt/Desktop/job017/particles.star'
output_folder = '/Users/matt/Desktop/test_picks'

# Dictionary to collect picks per micrograph
picks_by_micrograph = defaultdict(list)

with open(input_star_file, 'r') as f:
    lines = f.readlines()

# Locate start of particle data
data_started = False
for line in lines:
    if line.strip().startswith("data_particles"):
        data_started = True
    elif data_started and line.strip().startswith("loop_"):
        continue
    elif data_started and line.strip().startswith("_rln"):
        continue
    elif data_started and line.strip() and not line.startswith("#"):
        # Process data line
        parts = line.strip().split()
        if len(parts) < 7:
            continue  # skip malformed lines
        x = float(parts[0])
        y = float(parts[1])
        micrograph_name = parts[6]  # _rlnMicrographName
        picks_by_micrograph[micrograph_name].append((x, y))

# Write one TSV file per micrograph
for micrograph, picks in picks_by_micrograph.items():
    # Create safe filename (remove directory path and change extension)
    base_name = os.path.basename(micrograph)
    output_name = os.path.splitext(base_name)[0] + '_picks.tsv'

    with open(os.path.join(output_folder, output_name), 'w') as out:
        out.write("x\ty\n")
        for x, y in picks:
            out.write(f"{x:.6f}\t{(3200-y):.6f}\n")

    print(f"Wrote {len(picks)} picks to {output_name}")
