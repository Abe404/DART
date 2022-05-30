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


def create_jacobian(moving_image_dir_path):
    deformable_transform = os.path.join(moving_image_dir_path, 'registered1Warp.nii.gz')
    output_path = os.path.join(moving_image_dir_path, 'jacobian.nii.gz')
    cmd = (f'CreateJacobianDeterminantImage 3 {deformable_transform} {output_path}')
    print(cmd)
    os.system(cmd)


def compute_jacobian_for_all_patients(in_dir, planning_dir_name, patient_dir):
    """
        in_dir  - directory containing all the patient folders.
        planning_dir_name - folder containing the fixed image.
    """
    patient_dirs = os.listdir(in_dir)
    if patient_dir:
        patient_dirs = [patient_dir]
        print('Running on', patient_dirs, 'only')

    for patient in patient_dirs:
        patient_path = os.path.join(in_dir, patient)
        fraction_dirs = os.listdir(patient_path)
        fraction_dirs = [d for d in fraction_dirs if d != planning_dir_name]

        for fraction_dir in fraction_dirs:
            fraction_path = os.path.join(patient_path, fraction_dir)
            create_jacobian(moving_image_dir_path=fraction_path)

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Compute Jacobian for all transforms for all patients",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir", help="Name of directory containing the "
                                         "planning scan (fixed image)")
    parser.add_argument("--patient-dir", type=str, required=False,
                        help="patient to process (useful for testing)")
    args = parser.parse_args()
    config = vars(args)
    print(config)
    compute_jacobian_for_all_patients(config['input'],
                                      config['plan_dir'],
                                      config['patient_dir'])
