#!/bin/bash
#SBATCH --nodes 1
#SBATCH --job-name WANDB_PINN
#SBATCH -o batch_output.log
#SBATCH -e batch_error.log
#SBATCH --gres=gpu:1
#SBATCH --account=scw1901
#SBATCH --partition=accel_ai

source /scratch/s.1915438/env/modulus/bin/activate

wandb agent prakhars962/HIVE_first_trial/cqo23nt8
