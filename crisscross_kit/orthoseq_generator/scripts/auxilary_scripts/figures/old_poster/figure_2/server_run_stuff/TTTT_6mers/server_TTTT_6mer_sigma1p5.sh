#!/bin/bash
#SBATCH -c 20
#SBATCH --mem=20G
#SBATCH -t 35:00:00
#SBATCH --job-name=server_TTTT_6mer_sigma1p5
#SBATCH -o server_TTTT_6mer_sigma1p5_%j.out
#SBATCH -e server_TTTT_6mer_sigma1p5_%j.err
#SBATCH -p medium
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=florian_katzmeier@dfci.hms.edu

module load conda/miniforge3/24.11.3-0
conda activate cc
python -u Hash-CAD/crisscross_kit/orthoseq_generator/scripts/figures/figure_2/run_pipeline.py --config TTTT_6mer_sigma1p5.toml
