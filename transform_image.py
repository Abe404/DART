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


Take the transformations that have already been computed by 
compute_ants_registrations.py and use them to transform the
moving image files (such as dose or struct) to the fixed image.
"""

import os
import argparse
import time


def transform_moving_image_to_fixed_image(moving_image_dir_path,
                                          moving_image_file_name,
                                          planning_dir_name,
                                          fixed_image_path):
    """
    Transforms for one fraction

    moving_image_dir_path - most likely the path to the fraction directory
    moving_image_file_name - name of the moving_image file (assumed consistent for all fractions)
    fixed_image_path - full path to the fixed image. likely a 
                       reference scan used for computing the registration.
    """

    start_time = time.time()
    output_path = os.path.join(moving_image_dir_path, 
        f'{os.path.basename(moving_image_file_name.replace(".nii.gz", ""))}'
        f'_transformed_to_{planning_dir_name}.nii.gz')

    moving_image_path = os.path.join(moving_image_dir_path, moving_image_file_name)
    
    # tranforms moving image to fixed image
    deformable_transform = os.path.join(moving_image_dir_path, 'registered1Warp.nii.gz')
    affine_transform = os.path.join(moving_image_dir_path, 'registered0GenericAffine.mat')

    cmd = (f'antsApplyTransforms -d 3 -i {moving_image_path} '
           f'-o {output_path} -r {fixed_image_path} '
           f'-t {deformable_transform} -t {affine_transform}')

    print(cmd)
    os.system(cmd)
    print(f'time for {moving_image_dir_path}: {time.time() - start_time} seconds')


def transform_moving_images_to_fixed_images(in_dir, planning_dir_name,
                                    moving_image_file_name,
                                    fixed_image_name, first_n, patient_dir):
    """
        Transforms for all patients. 
        in_dir  - directory containing all the patient folders.
        planning_dir_name - folder containing the fixed image.
        moving_image_file_name - name of the actual moving_image file. We assume this is the
                         same for all fractions (and the planning scan),
                         with unique details being stored in the folder names.
        fixed_image_name - The name of the image that was used as 
                           the fixed image for computing the transform.
        first_n - used to restrict processing for testing/debugging.
    """
    patient_dirs = os.listdir(in_dir)

    if first_n:
        patient_dirs = patient_dirs[:first_n]

    if patient_dir:
        patient_dirs = [patient_dir]
        print('Running on', patient_dirs, 'only')

    for patient in patient_dirs:
        patient_path = os.path.join(in_dir, patient)
        fraction_dirs = os.listdir(patient_path)
        fraction_dirs = [d for d in fraction_dirs if d != planning_dir_name]

        for fraction_dir in fraction_dirs:
            fraction_path = os.path.join(patient_path, fraction_dir)
            transform_moving_image_to_fixed_image(
                moving_image_dir_path=fraction_path,
                moving_image_file_name=moving_image_file_name,
                planning_dir_name=planning_dir_name,
                fixed_image_path=os.path.join(patient_path, planning_dir_name, fixed_image_name))

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Apply ANTS transforms to transfer moving_image to fixed image",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir", help="Name of directory containing the "
                                         "planning scan (fixed image)")
    parser.add_argument("moving_image_file_name",
                        help="Name of the moving_image files that will be transformed,"
                             " assumed same for all fractions.")
    parser.add_argument("fixed_image_name",
                        help="Name of the fixed image that was used for "
                             "creating the transform, assumed same for all fractions.")

    parser.add_argument("--first-n", type=int, required=False,
                        help="first n, number of patients to process (useful for testing)")
    parser.add_argument("--patient-dir", type=str, required=False,
                        help="patient to process (useful for testing)")

    args = parser.parse_args()
    config = vars(args)
    print(config)
    transform_moving_images_to_fixed_images(config['input'], config['plan_dir'],
                                            config['moving_image_file_name'],
                                            config['fixed_image_name'],
                                            config['first_n'],
                                            config['patient_dir'])
