# source activate_env.sh

export python_path=/work2/07059/jyzhao/stampede3/run_pyrecodes/virtural_env/bin/python
export OMP_NUM_THREADS=32


ibrun -n 2 python /work2/07059/jyzhao/stampede3/run_pyrecodes/run_pyrecodes_parallel.py \
    --mainFile /work2/07059/jyzhao/stampede3/run_pyrecodes/input_data_common/Alameda_Main.json \
    --SystemConfigurationDir /work2/07059/jyzhao/stampede3/run_pyrecodes/system_config_samples \
    --SystemConfigurationBasename Alameda_SystemConfiguration \
    --ComponentLibraryFile /work2/07059/jyzhao/stampede3/run_pyrecodes/input_data_common/Alameda_ComponentLibrary.json \
    --r2dRunDir /work2/07059/jyzhao/stampede3/run_pyrecodes/run_dir/results \
    --inputDataDir /work2/07059/jyzhao/stampede3/run_pyrecodes/input_data_common \
    --outputDir /work2/07059/jyzhao/stampede3/run_pyrecodes/output_dir \
    --savePickleFile True