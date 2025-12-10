#!/usr/bin/env python3

from pathlib import Path
import csv

def main():
    # Define paths
    base_dir = Path(__file__).resolve().parents[1]  # Go up from auxilary_scripts
    input_file = base_dir /  "results" / "handles_with_energies.csv"  # Change name if needed
    output_file = base_dir /  "results" / "the_new_64_seq.txt"

    sequences = []

    # Read the CSV and extract handle and antihandle
    with open(input_file, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            handle = "TT" + row["handles"]
            antihandle = "TT" + row["antihandles"]
            sequences.append((handle, antihandle))

    # Write output as tab-separated file
    with open(output_file, "w") as outfile:
        for h1, h2 in sequences:
            outfile.write(f"{h1}\t{h2}\n")

    print(f"File written to: {output_file}")

if __name__ == "__main__":
    main()
