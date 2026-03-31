import pandas as pd
import numpy as np
from pathlib import Path

def rotate_180(matrix):
    """Rotate matrix 180 degrees"""
    return np.rot90(matrix, 2)

def mirror_horizontal(matrix):
    """Mirror matrix horizontally (left-right)"""
    return np.fliplr(matrix)

def mirror_vertical(matrix):
    """Mirror matrix vertically (up-down)"""
    return np.flipud(matrix)

def transform_csv(input_file):
    """
    Read CSV file and generate three transformations.
    Outputs files in the same directory with suffixes:
    - _rotation180.csv
    - _hmirrored.csv
    - _vmirrored.csv
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: File '{input_file}' not found.")
        return
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_path, header=None)
        matrix = df.values
        print(f"Processing: {input_path.name}")
        print(f"  Matrix shape: {matrix.shape}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Create output filenames by replacing extension
    base_name = input_path.stem  # filename without extension
    output_dir = input_path.parent
    
    # Apply transformations
    rotated = rotate_180(matrix)
    h_mirrored = mirror_horizontal(matrix)
    v_mirrored = mirror_vertical(matrix)
    
    # Save transformed matrices
    try:
        output_files = {
            output_dir / f"{base_name}_rotation180.csv": rotated,
            output_dir / f"{base_name}_hmirrored.csv": h_mirrored,
            output_dir / f"{base_name}_vmirrored.csv": v_mirrored,
        }
        
        for filepath, transformed_matrix in output_files.items():
            pd.DataFrame(transformed_matrix).to_csv(filepath, header=False, index=False)
            print(f"  ✓ {filepath.name}")
        
    except Exception as e:
        print(f"Error saving files: {e}")

# Main execution
if __name__ == "__main__":
    source_file_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/Stella/SW155_largescale_repeatingunits_90deg/domains'
    
    filenames = [f"SW155_RU_domain{x}_rotation0.csv" for x in range(1, 4)]
    
    print("Starting matrix transformations...\n")
    
    for filename in filenames:
        input_path = Path(source_file_folder) / filename
        transform_csv(input_path)
    
    print("\nAll transformations complete!")
