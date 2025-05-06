import os
import random
from collections import defaultdict
import pandas as pd

def extract_kmers(sequence, k):
    """Extract all kmers of length k from a given sequence."""
    return [sequence[i:i+k] for i in range(len(sequence) - k + 1)]

def find_kmers(sequence, k):
    """Find all kmers of length k in a sequence."""
    return [sequence[i:i+k] for i in range(len(sequence) - k + 1)]

def find_most_common_line(reoccurring_kmers):
    """Find the line with the most reoccurrences."""
    line_counts = defaultdict(int)
    for kmer, locations in reoccurring_kmers.items():
        for line, _ in locations:
            line_counts[line] += 1
    # Find the maximum count
    max_count = max(line_counts.values(), default=0)
    # Find lines with the maximum count
    most_common_lines = [line for line, count in line_counts.items() if count == max_count]
    # Return one line randomly if there is a tie
    return random.choice(most_common_lines) if most_common_lines else None

def flip_line(sequence_pairs, line_to_flip):
    """Flip the handle and antihandle in the specified line."""
    handle, antihandle = sequence_pairs[line_to_flip - 1]
    sequence_pairs[line_to_flip - 1] = (antihandle, handle)

def count_kmers_with_line_numbers_in_handles(sequence_pairs, k):
    """Count occurrences of k-mers in the handle column only."""
    kmer_locations = defaultdict(list)
    for line_idx, (handle, _) in enumerate(sequence_pairs):
        kmers = find_kmers(handle, k)
        for kmer in kmers:
            kmer_locations[kmer].append((line_idx + 1, "handle"))
    # Filter to keep only k-mers that appear more than once
    return {kmer: locations for kmer, locations in kmer_locations.items() if len(locations) > 1}

def save_results(sequence_pairs, flipped_lines, output_file):
    """Save the flipped sequences and flipped lines to a file."""
    flipped_file = output_file + "_flipped.txt"
    log_file = output_file + "_log.txt"

    # Save flipped sequence pairs
    with open(flipped_file, 'w') as f:
        for handle, antihandle in sequence_pairs:
            f.write(f"{handle}\t{antihandle}\n")

    # Save log of flipped lines
    with open(log_file, 'w') as f:
        for line, sequences in flipped_lines:
            f.write(f"Line {line}: {sequences}\n")

    print(f"Results saved to {flipped_file} and {log_file}")

if __name__ == "__main__":
    file_name = "TT_no_crosscheck96to104_64_sequence_pairs.txt"
    output_file = os.path.splitext(file_name)[0]

    # Load sequence pairs from file
    with open(file_name, 'r') as file:
        sequence_pairs = [line.strip().split('\t') for line in file.readlines()]

    # Initial repeated k-mers before any flips
    k = 5
    repeated_kmers = count_kmers_with_line_numbers_in_handles(sequence_pairs, k)

    # Print initial reoccurrences for inspection
    print("Initial repeated k-mers:")
    for kmer, locations in repeated_kmers.items():
        print(f"{kmer}: {locations}")

    # Run the flipping algorithm
    max_iterations = 190000
    iterations = 0
    changes = True
    flipped_lines = []

    while iterations < max_iterations and changes:
        # Recalculate repeated k-mers in the handle column
        repeated_kmers = count_kmers_with_line_numbers_in_handles(sequence_pairs, k)

        # Find the most common line among the reoccurrences
        line_to_flip = find_most_common_line(repeated_kmers)

        if line_to_flip:
            # Record the flip
            flipped_lines.append((line_to_flip, sequence_pairs[line_to_flip - 1]))
            flip_line(sequence_pairs, line_to_flip)
            iterations += 1
        else:
            changes = False

    # Final results: reoccurring k-mers after flipping
    final_repeated_kmers = count_kmers_with_line_numbers_in_handles(sequence_pairs, k)

    # Save the results
    save_results(sequence_pairs, flipped_lines, output_file)

    # Format final results for display
    final_repeated_kmers_df = pd.DataFrame(
        [(kmer, locations) for kmer, locations in final_repeated_kmers.items()],
        columns=["5-mer", "Locations (Line, Type)"]
    )

    print("Final repeated k-mers after flipping:")
    print(final_repeated_kmers_df)
