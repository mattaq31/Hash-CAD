def create_o2_slurm_file(command,
                         num_cpus,
                         memory,
                         time_length,
                         user_email='matthew_aquilina@dfci.harvard.edu'):
    """
    Description TBC
    :param command:
    :param num_cpus:
    :param memory:
    :param time_length:
    :param user_email:
    :return:
    """
    if time_length < 12:
        partition = 'short'
    else:
        partition = 'medium'

    main_command = f"""#!/bin/bash
#SBATCH -c {num_cpus}
#SBATCH --mem={memory}G
#SBATCH -t {time_length}:00:00
#SBATCH -p {partition}
#SBATCH --mail-type=ALL            
#SBATCH --mail-user={user_email}

module load miniconda3
source activate crisscross
 
{command}
"""

    return main_command
