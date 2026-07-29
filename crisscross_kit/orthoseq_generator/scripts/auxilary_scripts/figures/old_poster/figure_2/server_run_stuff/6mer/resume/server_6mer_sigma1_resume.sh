#!/bin/bash
#SBATCH -c 8
#SBATCH --mem=20G
#SBATCH -t 48:00:00
#SBATCH -p medium
#SBATCH -J 6mer_sigma1_resume
#SBATCH -o slurm-%x-%j.out
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=florian_katzmeier@dfci.hms.edu

module load conda/miniforge3/24.11.3-0
conda activate cc
python -u Hash-CAD/crisscross_kit/orthoseq_generator/scripts/figures/figure_2/run_pipeline.py --config 6mer_sigma1_resume.toml
