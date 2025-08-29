import os
import shutil
import re


def rename_and_move_files(input_folder, output_folder, add_number=4000):
    """
    Rename Excel files of the form best_handle_array_generation_<n>.xlsx
    by adding `add_number` to <n> and move them to the target folder.

    Parameters:
        input_folder (str): Path to the folder containing the original files.
        output_folder (str): Path to the folder where renamed files will be placed.
        add_number (int): The number to add to the numeric suffix (default: 4000).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.startswith("best_handle_array_generation_") and filename.endswith(".xlsx"):
            # Extract number using regex
            match = re.search(r"(\d+)\.xlsx$", filename)
            if match:
                old_number = int(match.group(1))
                new_number = old_number + add_number
                new_filename = f"best_handle_array_generation_{new_number}.xlsx"

                src = os.path.join(input_folder, filename)
                dst = os.path.join(output_folder, new_filename)

                shutil.copy2(src, dst)  # or use os.rename if you want to move instead of copy
                print(f"Renamed {filename} → {new_filename}")



if __name__ == '__main__':

    rename_and_move_files(
        input_folder="D:\Wyss_experiments\Evolution_analysis\evo_run_hexagon_2_12000_onward",
        output_folder="D:\Wyss_experiments\Evolution_analysis\evo_run_hexagon_2",
        add_number=12000
    )