#!/usr/bin/env bash

module purge
module load stack/2024-06 gcc/12.2.0
module load openmpi/4.1.6
module load python/3.11.6
source $HOME/run_pyrecodes/venv/bin/activate

export MPLBACKEND=Agg
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export pyrecodes_input_dir_common=$HOME/run_pyrecodes/input_data_common
