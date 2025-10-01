from pathlib import Path
import shutil
import glob
import ujson as json
import os
import sys
import pickle
from tqdm import tqdm
import argparse

import subprocess
import shlex
from mpi4py import MPI

THIS_DIR = Path(__file__).resolve().parent # yyh

def run_pyrecodes(  # noqa: C901
        main_file,
        system_config_dir,
        system_config_basefile,
        component_library_dir,
        component_library_basefile,
        r2d_run_dir,
        input_data_dir,
        environment_shell_script,
        output_dir,
        realization,
        save_pickle_file,
        calculation_single_process_file = str(THIS_DIR / "run_pyrecodes_single_proc.py") # yyh
):
    """
    Run pyrecodes simulation.

    Parameters
    ----------
    main_file (str): Path to the main configuration file.
    system_config_file (str): Path to the system file.
    component_library (str): Path to the component library file.
    locality_geojson (str): Path to the locality geojson file.
    """
    # Assume Results_det.json and Results_rlz.json are in rwhale run dir
    # This script is call in rwhale run dir
    if r2d_run_dir is None:
        run_dir = Path.cwd()
    else:
        run_dir = Path(r2d_run_dir)

    if input_data_dir is not None:
        input_data_dir = Path(input_data_dir)
    else:
        input_data_dir = Path(os.getcwd()).parent / 'input_data'
    if not Path(input_data_dir).exists():
        raise RuntimeError(f"Input data directory {input_data_dir} does not exist.")

    os.environ["pyrecodes_input_dir_common"] = str(input_data_dir)

    python_path = os.getenv("python_path")
    
    if not python_path:
      python_path = sys.executable

    comm = MPI.COMM_WORLD
    numP = comm.Get_size()  # noqa: N806
    procID = comm.Get_rank()  # noqa: N806
    
    # At least one of the system configuration dir or component library dir must be provided
    if system_config_dir == str(input_data_dir) and component_library_dir == str(input_data_dir):
        raise RuntimeError("At least one of the system configuration dir or component library dir must be provided and different from input data dir.")

    if component_library_dir != str(input_data_dir):
        component_library_path_samples = glob.glob(os.path.join(component_library_dir, f"{component_library_basefile}*.json"))
        component_library_filename_samples = [os.path.basename(x) for x in component_library_path_samples]
        sample_id_list_cl = [int(x.split(".")[0].split("_")[-1]) for x in component_library_filename_samples]

    if system_config_dir != str(input_data_dir):
        system_config_path_samples = glob.glob(os.path.join(system_config_dir, f"{system_config_basefile}*.json"))
        system_config_filename_samples = [os.path.basename(x) for x in system_config_path_samples]
        sample_id_list_sc = [int(x.split(".")[0].split("_")[-1]) for x in system_config_filename_samples]

    if component_library_dir != str(input_data_dir) and system_config_dir != str(input_data_dir):
        if set(sample_id_list_cl) != set(sample_id_list_sc):
            raise RuntimeError("The sample ids in the system configuration dir and component library dir do not match.")
        sample_id_list = sample_id_list_cl
    elif component_library_dir != str(input_data_dir):
        sample_id_list = sample_id_list_cl
    elif system_config_dir != str(input_data_dir):
        sample_id_list = sample_id_list_sc

    output_dir = Path(output_dir)
    temp_dir = output_dir / "temp"   # yyh

    if procID == 0:    
        if output_dir.exists():
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)

        # Modify the loss values in the Results_rlz.json file so that the
        # loss values are a small number if the damage is nonzero but loss is zero
        # This needs to be removed once the pyrecodes is updated to handle this
        rlz_lists = glob.glob(os.path.join(run_dir, f"Results_*.json"))
        if os.path.join(run_dir, "Results_det.json") in rlz_lists:
            rlz_lists.remove(os.path.join(run_dir, "Results_det.json"))
        for rlz in tqdm(rlz_lists, desc='Modify results_rlz files'):
            with Path(rlz).open() as f:
                results_rlz = json.load(f)
            for asset_type_dict in results_rlz.values():
                for asset_subtype_dict in asset_type_dict.values():
                    for asset_id_dict in asset_subtype_dict.values():
                        # damage_dict = asset_id_dict['Damage']
                        if 'Loss' in asset_id_dict:
                            loss_dist = asset_id_dict['Loss']
                            for comp in loss_dist['Repair']['Cost']:
                                # A minimum cost of 0.00001 is set to avoid division by zero
                                loss_dist['Repair']['Cost'][comp] = max(loss_dist['Repair']['Cost'][comp], 0.00001)
                            for comp in loss_dist['Repair']['Time']:
                                # A minimum time of 0.00001 is set to avoid division by zero
                                loss_dist['Repair']['Time'][comp] = max(loss_dist['Repair']['Time'][comp], 0.00001)
            with Path(rlz).open('w') as f:
                json.dump(results_rlz, f)

        temp_dir.mkdir(parents=True, exist_ok=True) # yyh

    comm.Barrier()

    for i, sample_id in tqdm(enumerate(sample_id_list)):
        if i % numP == procID:
            output_dir_i = output_dir / str(sample_id)
            os.mkdir(output_dir_i)

            if system_config_dir == str(input_data_dir):
                system_config_path = os.path.join(input_data_dir, f"{system_config_basefile}.json")
            else:
                system_config_path = os.path.join(system_config_dir, f"{system_config_basefile}_{sample_id}.json")
            if component_library_dir == str(input_data_dir):
                component_library = os.path.join(input_data_dir, f"{component_library_basefile}.json")
            else:
                component_library = os.path.join(component_library_dir, f"{component_library_basefile}_{sample_id}.json")

            command = f"{python_path} {calculation_single_process_file}"
            command += f" --mainFile {main_file}"
            command += f" --SystemConfigurationFile {system_config_path}"
            command += f" --ComponentLibraryFile {component_library}"
            command += f" --r2dRunDir {r2d_run_dir}"
            command += f" --inputDataDir {input_data_dir}"
            command += f" --outputDir {output_dir_i}"
            #command += f" > /work2/07059/jyzhao/stampede3/run_pyrecodes/temp/sh_file_{sample_id}.out 2>&1"
            command += f" > {temp_dir}/sh_file_{sample_id}.out 2>&1" #yyh

            print(command)
            #sh_file_path = f"/work2/07059/jyzhao/stampede3/run_pyrecodes/temp/sh_file_{sample_id}.sh"
            sh_file_path = str(temp_dir / f"sh_file_{sample_id}.sh")  #yyh
            with open(sh_file_path, 'w') as sh_file:
                sh_file.write("#!/bin/bash\n")
                sh_file.write(f"source {environment_shell_script}\n")
                sh_file.write(f"{command}\n")
                # sh_file.write(f'''exec >"/work2/07059/jyzhao/stampede3/run_pyrecodes/temp/sh_file_{sample_id}.out" 2>&1''')
                
            try:
                subprocess.run(["chmod", "+x", sh_file_path])
                result = subprocess.check_output(["bash", "-c", f"source {sh_file_path}"], shell=False)
                # Check if the script ran successfully
                # os.remove(sh_file_path)
            except subprocess.CalledProcessError as e:
                # os.remove(sh_file_path)
                sys.exit(f'return code: {e.output}')


if __name__ == '__main__':
    # Defining the command line arguments

    workflowArgParser = argparse.ArgumentParser(  # noqa: N816
        'Run Pyrecodes parallel.',
        allow_abbrev=False,
    )

    workflowArgParser.add_argument(
        '--savePickleFile', required=False,
        default=False,
        help='If save all pyrecodes results as a pickle file.',
    )

    workflowArgParser.add_argument(
        '--mainFile', help='Pyrecodes main file', required=False
    )

    workflowArgParser.add_argument(
        '--SystemConfigurationDir', help='Director containing system configuration realizations', required=True
    )

    workflowArgParser.add_argument(
        '--SystemConfigurationBasename', help='Basename of system configuration realization files', required=True
    )

    workflowArgParser.add_argument(
        '--ComponentLibraryDir', help='Director containing component library files', required=True
    )

    workflowArgParser.add_argument(
        '--ComponentLibraryBasename', help='Basename of component library files', required=True
    )

    workflowArgParser.add_argument(
        '--localityGeojsonFile',
        default=None,
        help='Geojson defining the locality of the assets',
    )

    workflowArgParser.add_argument(
        '--r2dRunDir',
        default=None,
        help='R2D run directory containing the results',
    )

    workflowArgParser.add_argument(
        '--inputDataDir',
        default=None,
        help='R2D input data directory',
    )

    workflowArgParser.add_argument(
        '--outputDir',
        required=True,
        help='The directory to save outputs'
    )

    workflowArgParser.add_argument(
        '--environmentShellScript',
        required=True,
        help='The path to the shell script to set up the environment'
    )

    workflowArgParser.add_argument(
        '--mpiexec',
        default='ibrun',
        help='How mpi runs, e.g. ibrun, mpirun, mpiexec',
    )
    workflowArgParser.add_argument(
        '--numP',
        default='8',
        help='If parallel, how many jobs to start with mpiexec option',
    )

    # Parsing the command line arguments
    wfArgs = workflowArgParser.parse_args()  # noqa: N816


    run_pyrecodes(
        main_file=wfArgs.mainFile,
        system_config_dir=wfArgs.SystemConfigurationDir,
        system_config_basefile=wfArgs.SystemConfigurationBasename,
        component_library_dir=wfArgs.ComponentLibraryDir,
        component_library_basefile=wfArgs.ComponentLibraryBasename,
        r2d_run_dir=wfArgs.r2dRunDir,
        input_data_dir=wfArgs.inputDataDir,
        environment_shell_script=wfArgs.environmentShellScript,
        output_dir=wfArgs.outputDir,
        realization=None,
        save_pickle_file=wfArgs.savePickleFile
    )
