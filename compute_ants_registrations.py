"""
Copyright (C) 2022 Abraham George Smith
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import argparse
import time

def compute_all_registrations(in_dir, planning_scan_dir_name, scan_name, first_n):
    # scan_name is the name of the actual scan file. We assume this is the
    # same for all fractions (and the planning scan), with unique details being stored
    # in the folder names.
    patient_dirs = os.listdir(in_dir)

    if first_n:
        patient_dirs = patient_dirs[:first_n]

    for patient_dir in patient_dirs:
        patient_path = os.path.join(in_dir, patient_dir)
        fraction_dirs = os.listdir(patient_path)
        fraction_dirs = [d for d in fraction_dirs if d != planning_scan_dir_name]
        
        for fraction_dir in fraction_dirs:
            start_time = time.time()
            fraction_scan_path = os.path.join(in_dir, patient_dir,
                                              fraction_dir, scan_name)
            planning_scan_path = os.path.join(in_dir, patient_dir,
                                              planning_scan_dir_name,
                                              scan_name)

            # output files will be called 'registered' and exist in the fraction directory.
            output_path = os.path.join(in_dir, patient_dir,
                                       fraction_dir, 'registered')

            # for documentation on antsRegistrationSyN.sh see:
            # https://github.com/ANTsX/ANTs/blob/master/Scripts/antsRegistrationSyN.sh 

            # register the fraction (moving image) to the planning scan (fixed image)
            cmd = (f'antsRegistrationSyN.sh -d 3 '
                   '-t s ' # transform type s:  rigid_affine+deformable syn (3 stages)'
                   f'-n {os.cpu_count()} ' # number of threads to use.
                   f'-f {planning_scan_path} -m {fraction_scan_path} '
                   # This output_path supplied (defined above) is used as 
                   # the OUTPUTNAME variable in antsRegistrationSyn.sh script, which 
                   # is then used to create the following output argument
                   # for the antsRegistration executable.
                   # [ $OUTPUTNAME,${OUTPUTNAME}Warped.nii.gz,${OUTPUTNAME}InverseWarped.nii.gz ]
                   # This output argument is document as follows, taken from antsRegistration docs:
                   #
                   # -o, --output outputTransformPrefix
                   #     [outputTransformPrefix,<outputWarpedImage>,<outputInverseWarpedImage>]
                   #     Specify the output transform prefix (output format is
                   #     .nii.gz ). Optionally, one can choose to warp the
                   #     moving image to the fixed space and, if the inverse
                   #     transform exists, one can also output the warped fixed
                   #     image. Note that only the images specified in the first
                   #     metric call are warped. Use antsApplyTransforms to warp
                   #     other images using the resultant transform(s). When a
                   #     composite transform is not specified, linear transforms
                   #     are specified with a '.mat' suffix and displacement
                   #     fields with a 'Warp.nii.gz' suffix (and
                   #     'InverseWarp.nii.gz', when applicable. In addition, for
                   #     velocity-based transforms, the full velocity field is
                   #     written to file ('VelocityField.nii.gz') as long as the
                   #     collapse transforms flag is turned off ('-z 0').
                   #
                   # From the above docs we can see that <outputWarpedImage> is the moving image
                   # transformed to the fixed image. Which in our case is the fraction
                   # transformed to the MR SIM.
                   # Concretely, in our case the fraction scan warped to the MR sim will be
                   # named registeredWarped.nii.gz
                   f'-o {output_path}')

            print(cmd)
            os.system(cmd)
            print(f'time for {fraction_dir},{patient_dir}: {time.time() - start_time} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Compute ANTS transforms to register fractions to planning scan",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir", help="Name of directory containing the "
                                         "planning scan (reference image)")
    parser.add_argument("scan_name", help="Name of the scan files that will be registered,"
                                          " assumed same for all fractions.")
    parser.add_argument("--first-n", type=int, required=False,
                        help="first n, number of patients to process (useful for testing)")
    args = parser.parse_args()
    config = vars(args)
    print(config)
    compute_all_registrations(config['input'], config['plan_dir'],
                              config['scan_name'], config['first_n'])
