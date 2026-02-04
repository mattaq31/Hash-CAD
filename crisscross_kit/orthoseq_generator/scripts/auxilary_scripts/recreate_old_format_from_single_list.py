#!/usr/bin/env python3

from pathlib import Path
import csv
import sequence_computations as sc

def main():
    # Define paths
    base_dir = Path(__file__).resolve().parents[1]  # Go up from auxilary_scripts
    input_file = base_dir /  "results" / "stell.txt"  # Change name if needed
    output_file = base_dir /  "results" / "stell_2.txt"

    sequences = []

    # Read the CSV and extract handle and antihandle
    with open(input_file, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            handle = row["handles"]
            antihandle = sc.revcom(handle)
            handle = 'TT'+ handle
            antihandle = 'TT'+ antihandle
            sequences.append((handle, antihandle))

    # Write output as tab-separated file
    with open(output_file, "w") as outfile:
        for h1, h2 in sequences:
            outfile.write(f"{h1}\t{h2}\n")

    print(f"File written to: {output_file}")

if __name__ == "__main__":
    main()