#!/usr/bin/env bash
#SBATCH --job-name=pyrecodes_parallel
#SBATCH --partition=normal.24h
#SBATCH --nodes=2
#SBATCH --ntasks=8
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=32
#SBATCH --time=24:00:00
#SBATCH --output=%x_%j.out

set -euo pipefail
echo "[JOB] start: $(date) on $(hostname)"
echo "[JOB] jobid=$SLURM_JOB_ID cpus=$SLURM_CPUS_PER_TASK"

HOME_PROJ="$HOME/run_pyrecodes"
SCRATCH_PROJ="/cluster/scratch/$USER/run_pyrecodes"

#
JOB_TAG="${SLURM_JOB_ID:-run}"
SCR_INPUT="$SCRATCH_PROJ/input_data_common"
SCR_RESULTS="$SCRATCH_PROJ/run_dir/results"
SCR_OUTPUT="$SCRATCH_PROJ/output_dir/$JOB_TAG"

mkdir -p "$SCR_INPUT" "$SCR_RESULTS" "$SCR_OUTPUT"

#
HOME_OUTPUT_BASE="$HOME_PROJ/output_dir"
HOME_OUTPUT="$HOME_OUTPUT_BASE/$JOB_TAG"
mkdir -p "$HOME_OUTPUT_BASE" 


# 
source "$HOME_PROJ/activate_env.sh"


rsync -a "$HOME_PROJ/input_data_common/" "$SCR_INPUT/"
rsync -a "$HOME_PROJ/run_dir/results/" "$SCR_RESULTS/"
rsync -a "$HOME_PROJ/system_config_samples/" "$SCRATCH_PROJ/system_config_samples/"
rsync -a "$HOME_PROJ/component_library_samples/" "$SCRATCH_PROJ/component_library_samples/"

#
mkdir -p "$SCRATCH_PROJ"
cd "$SCRATCH_PROJ"
echo "[JOB] workdir: $(pwd)"

#
srun python "$HOME_PROJ/run_pyrecodes_parallel.py" \
  --mainFile "$SCR_INPUT/Alameda_Main.json" \
  --SystemConfigurationDir "$SCRATCH_PROJ/input_data_common" \
  --SystemConfigurationBasename "Alameda_SystemConfiguration" \
  --ComponentLibraryDir "$SCRATCH_PROJ/component_library_samples" \
  --ComponentLibraryBasename "Alameda_ComponentLibrary" \
  --r2dRunDir "$SCR_RESULTS" \
  --inputDataDir "$SCR_INPUT" \
  --environmentShellScript "$HOME_PROJ/activate_env.sh" \
  --outputDir "$SCR_OUTPUT" \
  --savePickleFile True

#
echo "[JOB] syncing results ? $HOME_OUTPUT"
rsync -a "$SCR_OUTPUT/" "$HOME_OUTPUT/"

#
ln -sfn "$HOME_OUTPUT" "$HOME_OUTPUT_BASE/latest"

echo "[JOB] done: $(date)"