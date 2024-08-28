#!/bin/bash
#SBATCH --job-name=VirtualLab
#SBATCH --output=VL_out.txt
#SBATCH --error=VL_err.txt
#SBATCH --nodes 1
#SBATCH --gres=gpu:1
#SBATCH --account=scw1901
#SBATCH --partition=accel_ai_mig

module load apptainer


VirtualLab -f VirtualLab/RunFiles/Tutorials/HIVE/Task1_Run.py -K ShowMesh=False -K ShowRes=False
