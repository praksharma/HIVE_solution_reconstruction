#!/bin/bash
#SBATCH --nodes 1
#SBATCH --job-name HIVE_PINN
#SBATCH -o batch_output.log
#SBATCH -e batch_error.log
#SBATCH --gres=gpu:1
#SBATCH --account=scw1901
#SBATCH --partition=accel_ai_mig

source /scratch/s.1915438/env/modulus/bin/activate

jupyter nbconvert --execute --to notebook --inplace forward.ipynb
