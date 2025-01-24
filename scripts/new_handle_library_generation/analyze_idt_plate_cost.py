import os
import pandas as pd

# Folder containing all the Excel workbooks
input_folder = "/Users/matt/Desktop/IDT_order_plates"

def extract_number(filename):
    return int(filename.split('_P')[-1].split('_')[0])

# Get all Excel files in the folder and sort them by `PXXXX`
files = [f for f in os.listdir(input_folder) if f.endswith(".xlsx")]
sorted_files = sorted(files, key=extract_number)

plate_dna_length = {}
for file in sorted_files:
    plate_name = 'P' + file.split('_P')[-1].split('_')[0]
    plate_df = pd.read_excel(os.path.join(input_folder, file))
    plate_df['DNALength'] = plate_df['Sequence'].str.len()
    plate_dna_length[plate_name] = plate_df['DNALength'].sum()

total_dna_bases = 0
for length in plate_dna_length.values():
    total_dna_bases += length

price_per_19854_bases_william = 4032.35
price_per_19854_bases_edinburgh = 1850.69
price_per_19854_bases_aarhus = 22129.92

full_price_william = total_dna_bases / 19854 * price_per_19854_bases_william
full_price_edinburgh = total_dna_bases / 19854 * price_per_19854_bases_edinburgh
full_price_aarhus = total_dna_bases / 19854 * price_per_19854_bases_aarhus

print(f"Total DNA bases in complete handle library (64 handles, H5-handles, H2-antihandles): {total_dna_bases}")
print(f"Total price (William): {full_price_william:.2f}$")
print(f"Price per base (William): {price_per_19854_bases_william/19854:.2f}$")
print('--')
print(f"Total price (Edinburgh): {full_price_edinburgh:.2f}￡")
print(f"Total price (Edinburgh - dollars): {full_price_edinburgh*1.22:.2f}$")
print(f"Price per base (Edinburgh): {price_per_19854_bases_edinburgh/19854:.2f}￡")
print(f"Price per base (Edinburgh - dollars): {(price_per_19854_bases_edinburgh/19854)*1.22:.2f}$")
print('--')
print(f"Total price (Aarhus): {full_price_aarhus:.2f}kr.")
print(f"Total price (Aarhus - dollars): {full_price_aarhus*0.14:.2f}$")
print(f"Price per base (Aarhus): {price_per_19854_bases_aarhus/19854:.2f}kr.")
print(f"Price per base (Aarhus - dollars): {(price_per_19854_bases_aarhus/19854)*0.14:.2f}$")
