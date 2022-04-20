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


Note: Some of this script contains code modified from the mask_to_dicom_rtstruct project located at:
https://github.com/Abe404/mask_to_dicom_rtstruct/blob/main/dicom_utils.py

This script recieves an input folder that contains a folder of patients.
Each patient corresponds to folder of fractions.
Each fraction is a folder containing dicom files.
The dicom files for each fraction include files for the scan, dose and structure.
There may also be other files such as the plan which can be ignored.
"""
import argparse
import pydicom
import numpy as np
import os

def load_image_series(dicom_dir):
    """
    Get all dicom image dataset files for a dicom series in a dicom dir.
    """
    image_series = []
    dicom_files = sorted(os.listdir(dicom_dir))
    for f in dicom_files:
        fpath = os.path.join(dicom_dir, f)
        if os.path.isfile(fpath):
            fdataset = pydicom.dcmread(fpath)
            # Computed Radiography Image Storage SOP Class UID
            # https://dicom.nema.org/dicom/2013/output/chtml/part04/sect_B.5.html
            mr_sop_class_uid = '1.2.840.10008.5.1.4.1.1.4'
            ct_sop_class_uid = '1.2.840.10008.5.1.4.1.1.2'
            if fdataset.SOPClassUID in [mr_sop_class_uid, ct_sop_class_uid]:
                image_series.append(fdataset)
    return image_series


def get_3d_image(dicom_series_path):
    """ return dicom images as 3D numpy array 

        warning: this function assumes the file names
                 sorted alpha-numerically correspond to the
                 position of the dicom slice in the z-dimension (depth)

                 if this assumption does not hold then you may need
                 to sort them based on their metadata (actual position in space).
    """
    image_series_files = load_image_series(dicom_series_path)
    first_im = image_series_files[0]
    height, width = first_im.pixel_array.shape
    depth = len(image_series_files)
    image = np.zeros((depth, height, width))
    for i, im in enumerate(image_series_files):
        image[i] = im.pixel_array
    return image


def convert_scan_to_nifty(in_dir, out_dir, verbose):
    if verbose:
        print('convert scan to nifty. input fraction path', in_dir, 'output fraction path', out_dir)     


def convert_to_nifty(in_dir, out_dir, verbose=False):
    # if the output folder does not exist then create it
    if not os.path.isdir(out_dir):
        if verbose:
            print('creating output directory for exported patient data', out_dir)
        os.makedirs(out_dir)
    patient_dirs = os.listdir(in_dir)
    if verbose:
        print(f'found {len(patient_dirs)} patient directories')
    for patient_dir in patient_dirs:
        if verbose:
            print('processing', patient_dir)
        patient_path = os.path.join(in_dir, patient_dir)
        fraction_dirs = os.listdir(patient_path)
        for fraction_dir in fraction_dirs:
            fraction_path = os.path.join(in_dir, patient_dir, fraction_dir)
            if verbose:
                print('processing', fraction_path)
            output_path = os.path.join(out_dir, patient_dir, fraction_dir)
            convert_scan_to_nifty(fraction_path, output_path, verbose)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dicom conversion utility. Convert from dicom to nifty",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", help="Directory containing patient folders")
    parser.add_argument("output", help="Output location for nifty files")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")
    args = parser.parse_args()
    config = vars(args)
    convert_to_nifty(config['input'], config['output'], config['verbose'])
