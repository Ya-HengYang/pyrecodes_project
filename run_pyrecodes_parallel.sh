environmentShellScript=/work2/07059/jyzhao/stampede3/run_pyrecodes/activate_env.sh
source $environmentShellScript

export python_path=/work2/07059/jyzhao/stampede3/run_pyrecodes/virtural_env/bin/python
export OMP_NUM_THREADS=32

proj_dir=/work2/07059/jyzhao/stampede3/pyrecodes_project

ibrun -n 2 python $proj_dir/run_pyrecodes_parallel.py \
    --mainFile $proj_dir/input_data_common/Alameda_Main.json \
    --SystemConfigurationDir $proj_dir/input_data_common \
    --SystemConfigurationBasename Alameda_SystemConfiguration \
    --ComponentLibraryDir $proj_dir/component_library_samples \
    --ComponentLibraryBasename Alameda_ComponentLibrary \
    --r2dRunDir $proj_dir/run_dir/results \
    --inputDataDir $proj_dir/input_data_common \
    --outputDir $proj_dir/output_dir \
    --environmentShellScript /work2/07059/jyzhao/stampede3/run_pyrecodes/activate_env.sh \
    --savePickleFile True