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


Take the transformed doses that have already been created by 
transform_dose.py and sum them for each patient.
"""

import os
import argparse
import SimpleITK as sitk


def sum_doses_for_all_patients(in_dir, planning_dir_name,
                               plan_dose_file_name,
                               transformed_dose_file_name,
                               patient_dir,
                               summed_dose_file_name):
    """
        in_dir  - directory containing all the patient folders.
        planning_dir_name - folder containing the fixed image.
        dose_file_name - name of the actual dose file. We assume this is the
                         same for all fractions (and the planning scan),
                         with unique details being stored in the folder names.
        first_n - used to restrict processing for testing/debugging.
    """
    patient_dirs = os.listdir(in_dir)
    total_doses = 0
    if patient_dir:
        patient_dirs = [patient_dir]
        print('Running on', patient_dirs, 'only')

    for patient in patient_dirs:
        patient_path = os.path.join(in_dir, patient)
        fraction_dirs = [d for d in os.listdir(patient_path) if d != planning_dir_name]
        plan_dose_path = os.path.join(patient_path, planning_dir_name, plan_dose_file_name)
        dose_sum = sitk.ReadImage(plan_dose_path, sitk.sitkFloat32)
        for fraction_dir in fraction_dirs:
            fraction_dose_path = os.path.join(patient_path, fraction_dir,
                                              transformed_dose_file_name)
            dose_sum += sitk.ReadImage(fraction_dose_path, sitk.sitkFloat32)

    # save the summed dose in the planning dir name
    summed_dose_path = os.path.join(patient_path, planning_dir_name, summed_dose_file_name)
    print('Saving summed dose to', summed_dose_path)
    sitk.WriteImage(dose_sum, summed_dose_path)

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Sum transformed dose files",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir", help="Name of directory containing the "
                                         "planning scan (fixed image)")
    parser.add_argument("plan_dose_file_name",
                        help="First dose file for planning scan. For example on MR SIM.")
    parser.add_argument("transformed_dose_file_name",
                        help="Name of the dose files that will be summed,"
                             " assumed same for all fractions.")
    parser.add_argument("--patient-dir", type=str, required=False,
                        help="patient to process (useful for testing)")
    parser.add_argument("--output-name", type=str, required=True,
                        help="Name of output summed dose file. Saved in plan_dir")

    args = parser.parse_args()
    config = vars(args)
    print(config)
    sum_doses_for_all_patients(config['input'],
                               config['plan_dir'],
                               config['plan_dose_file_name'],
                               config['transformed_dose_file_name'],
                               config['patient_dir'],
                               config['output_name'])
