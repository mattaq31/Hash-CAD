def create_o2_slurm_file(command,
                         num_cpus,
                         memory,
                         time_length,
                         user_email='matthew_aquilina@dfci.harvard.edu'):
    """
    Creates a standard slurm batch file script and then adds the provided command at the end of the script.
    The script is specifically formatted for the O2 server, but can be adjusted for other servers.
    :param command: The string command to add at the end of the batch file
    :param num_cpus: Num of CPU cores to request
    :param memory: Memory in GB to request
    :param time_length: Time in hours to request (if < 12 hours, will be placed in short partition, otherwise medium)
    :param user_email: The email to which failure notifications will be sent
    :return: The full slurm batch file script (string)
    """
    if time_length <= 12:
        partition = 'short'
    else:
        partition = 'medium'

    main_command = f"""#!/bin/bash
#SBATCH -c {num_cpus}
#SBATCH --mem={memory}G
#SBATCH -t {time_length}:00:00
#SBATCH -p {partition}
#SBATCH --mail-type=FAIL            
#SBATCH --mail-user={user_email}

module load conda/miniforge3/24.11.3-0
conda activate crisscross
 
{command}
"""

    return main_command
