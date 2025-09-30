#!/usr/bin/env bash
set -e

source $HOME/run_pyrecodes/activate_env.sh


$HOME/run_pyrecodes/venv/bin/python $HOME/run_pyrecodes/run_pyrecodes_single_proc.py --mainFile $HOME/run_pyrecodes/input_data_common/Alameda_Main.json --SystemConfigurationFile $HOME/run_pyrecodes/system_config_samples/Alameda_SystemConfiguration_1.json --ComponentLibraryFile $HOME/run_pyrecodes/input_data_common/Alameda_ComponentLibrary.json --r2dRunDir $HOME/run_pyrecodes/run_dir/results --inputDataDir $HOME/run_pyrecodes/input_data_common --outputDir $HOME/run_pyrecodes/output_dir/1 #> ./temp/sh_file_1.out 2>&1
