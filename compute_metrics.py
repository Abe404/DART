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

Compute structure overlap metrics between fixed structure and
transformed structures from each fraction
"""

import os
import argparse
from medpy import metric
import numpy as np
import nibabel as nib


def compute_metrics_for_all_patients(input_dir,
                                     struct_file_name,
                                     planning_dir_name,
                                     transformed_struct_file_name,
                                     patient_dir,
                                     output_csv_path):

    patient_dirs = os.listdir(input_dir)
    if patient_dir:
        patient_dirs = [patient_dir]

    with open(output_csv_path, 'w+', encoding='utf-8') as metrics_file:
        print("patient,fraction,dice,hd95,precision,recall", file=metrics_file)
        for patient in patient_dirs:
            patient_path = os.path.join(input_dir, patient)
            fraction_dirs = [d for d in os.listdir(patient_path) if d != planning_dir_name]

            fixed_struct_path = os.path.join(patient_path,
                                             planning_dir_name,
                                             struct_file_name)

            fixed_struct = nib.load(fixed_struct_path).get_fdata()
            assert (a := np.min(fixed_struct)) == 0, a
            assert (a := np.max(fixed_struct)) == 1.0, a
            fixed_struct[fixed_struct < 0.5] = 0
            fixed_struct[fixed_struct >= 0.5] = 1

            for fraction_dir in fraction_dirs:
                compute_metrics_for_fraction(metrics_file, 
                                             fixed_struct,
                                             patient_path,
                                             patient,
                                             fraction_dir,
                                             transformed_struct_file_name)

def compute_metrics_for_fraction(metrics_file,
                                 fixed_struct,
                                 patient_path,
                                 patient,
                                 fraction_dir,
                                 transformed_struct_file_name):

    fraction_struct_path = os.path.join(patient_path, fraction_dir,
                                        transformed_struct_file_name)
    transformed_struct = nib.load(fraction_struct_path).get_fdata()
    transformed_struct[transformed_struct < 0.5] = 0
    transformed_struct[transformed_struct >= 0.5] = 1
    assert np.any(transformed_struct) and np.any(fixed_struct)

    dice = metric.binary.dc(transformed_struct, fixed_struct)
    hd = metric.binary.hd95(transformed_struct, fixed_struct)
    precision = metric.binary.precision(transformed_struct, fixed_struct)
    recall = metric.binary.recall(transformed_struct, fixed_struct)

    print(f"{patient},{fraction_dir},dice:{dice},"
          f"hd95:{hd},prec:{precision},recall:{recall}")
    print(f"{patient},{fraction_dir},{dice},"
          f"{hd},{precision},{recall}", file=metrics_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Compute overlap metrics for structures",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders (nifty files)")
    parser.add_argument("plan_dir", help="Name of directory containing the "
                                         "planning scan (reference image)")
    parser.add_argument("--fixed-struct-file-name", type=str, required=True,
                        help="File name of fixed struct")
    parser.add_argument("--transformed-struct-file-name", type=str, required=True,
        help="File name of transformed structs (assumed to be the same accross fractions).")
    parser.add_argument("--patient-dir", type=str, required=False,
                        help="patient to process (useful for testing)")

    parser.add_argument("--output-csv", type=str, required=True,
                        help="Path of output csv file")

    args = parser.parse_args()
    config = vars(args)
    compute_metrics_for_all_patients(
        config['input'],
        config['fixed_struct_file_name'],
        config['plan_dir'],
        config['transformed_struct_file_name'],
        config['patient_dir'],
        config['output_csv'])
