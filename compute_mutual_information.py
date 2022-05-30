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
from medpy import metric
import nibabel as nib


def compute_mi_for_all_patients(input_dir,
                                planning_dir_name,
                                fixed_scan_name,
                                transformed_scan_name,
                                patient_dir,
                                output_csv_path):

    patient_dirs = os.listdir(input_dir)
    if patient_dir:
        patient_dirs = [patient_dir]

    with open(output_csv_path, 'w+', encoding='utf-8') as metrics_file:
        print("patient,fraction,mutual_information", file=metrics_file)
        for patient in patient_dirs:
            patient_path = os.path.join(input_dir, patient)
            fraction_dirs = [d for d in os.listdir(patient_path) if d != planning_dir_name]

            fixed_scan_path = os.path.join(patient_path,
                                           planning_dir_name,
                                           fixed_scan_name)

            fixed_scan = nib.load(fixed_scan_path).get_fdata()

            for fraction_dir in fraction_dirs:
                compute_mi_for_fraction(metrics_file, 
                                        fixed_scan,
                                        patient_path,
                                        patient,
                                        fraction_dir,
                                        transformed_scan_name)

def compute_mi_for_fraction(metrics_file,
                            fixed_scan,
                            patient_path,
                            patient,
                            fraction_dir,
                            transformed_scan_name):

    fraction_scan_path = os.path.join(patient_path, fraction_dir,
                                      transformed_scan_name)
    transformed_scan = nib.load(fraction_scan_path).get_fdata()
    mutual_information = metric.image.mutual_information(fixed_scan, transformed_scan)
    print(f"{patient},{fraction_dir},mutual_information:{mutual_information}")
    print(f"{patient},{fraction_dir},{mutual_information}", file=metrics_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Compute mutual information between fixed image and transformed images",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir",
        help="Name of directory containing the " "planning scan (reference image)")
    parser.add_argument("--fixed-scan-name", type=str, required=True, help="Name of fixed scan")
    parser.add_argument("--transformed-scan-name", type=str, required=True,
        help="File name of transformed scans (assumed to be the same accross fractions).")
    parser.add_argument("--patient-dir", type=str, required=False,
                        help="patient to process (useful for testing)")
    parser.add_argument("--output-csv", type=str, required=True,
                        help="Path of output csv file")

    args = parser.parse_args()
    config = vars(args)
    compute_mi_for_all_patients(
        config['input'],
        config['plan_dir'],
        config['fixed_scan_name'],
        config['transformed_scan_name'],
        config['patient_dir'],
        config['output_csv'])
