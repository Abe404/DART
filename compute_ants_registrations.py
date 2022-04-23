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

def compute_all_registrations(in_dir, planning_scan_dir_name, scan_name):
    # scan_name is the name of the actual scan file. We assume this is the
    # same for all fractions (and the planning scan), with unique details being stored
    # in the folder names.
    patient_dirs = os.listdir(in_dir)[:2]
    input_paths = []
    output_paths = []
    for patient_dir in patient_dirs:
        patient_path = os.path.join(in_dir, patient_dir)
        fraction_dirs = os.listdir(patient_path)
        fraction_dirs = [d for d in fraction_dirs if d != planning_scan_dir_name]
        
        for fraction_dir in fraction_dirs:
            fraction_scan_path = os.path.join(in_dir, patient_dir,
                                              fraction_dir, scan_name)
            planning_scan_path = os.path.join(in_dir, patient_dir, planning_scan_dir_name, scan_name)

            # output files will be called 'registered' and exist in the fraction directory.
            output_path = os.path.join(in_dir, patient_dir, fraction_dir, 'registered')

            # for documentation on antsRegistrationSyN.sh see:
            # https://github.com/ANTsX/ANTs/blob/master/Scripts/antsRegistrationSyN.sh 

            # register the fraction (moving image) to the planning scan (fixed image)
            dimensions = 3
            os.system(f'antsRegistrationSyN.sh -d {dimensions} '
                      # transform type s:  rigid_affine+deformable syn (3 stages)'
                      '-t s '
                      f'-n {os.cpu_count()} ' # number of threads to use.
                      f'{planning_scan_path} {fraction_scan_path} {output_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Compute ANTS transforms to register fractions to planning scan",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir", help="Name of directory containing the planning scan (reference image)")
    parser.add_argument("scan_name", help="Name of the scan files that will be registered, assumed same for all fractions.")
    args = parser.parse_args()
    config = vars(args)
    print(config)
    compute_all_registrations(config['input'], config['plan_dir'], config['scan_name'])
