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

import os
from multiprocessing import Pool
from enum import Enum
import argparse
import time
import sys
import logging

import pydicom
import numpy as np
import nibabel as nib
from dicom_mask.convert import struct_to_mask

class ImageType(Enum):
    STRUCT = 1
    SCAN = 2
    DOSE = 3

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


def get_scan_image(dicom_series_path):
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


def get_dose_image(dicom_series_path):
    fnames = os.listdir(dicom_series_path)
    dose_dataset = None

    for f in fnames:
        fpath = os.path.join(dicom_series_path, f)
        if os.path.isfile(fpath):
            fdataset = pydicom.dcmread(fpath)
            # RT Dose Storage SOP Class UID
            # https://dicom.nema.org/dicom/2013/output/chtml/part04/sect_B.5.html
            rt_dose_sop_class_uid = '1.2.840.10008.5.1.4.1.1.481.2'
            if fdataset.SOPClassUID == rt_dose_sop_class_uid:
                if not dose_dataset:
                    dose_dataset = fdataset
                else:
                    raise Exception(f'Multiple dose files were found in {dicom_series_path}.'
                                    'Please delete all dose files except the one which '
                                    'you wish to accumulate.')
    if not dose_dataset:
        raise Exception(f'Could not find a dose dataset in {dicom_series_path}.')
    # Get the dose grid
    # Taking influence from: https://docs.pymedphys.com/_modules/pymedphys/_dicom/dose.html
    dose_dataset.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
    dose = dose_dataset.pixel_array * dose_dataset.DoseGridScaling
    return dose


def get_struct_image(dicom_series_path, struct_name):
    dicom_files = [d for d in os.listdir(dicom_series_path) if d.endswith('.dcm')]

    # We assume here that you identified a single struct for each fraction
    # and given it the same name in all fractions in order for it to be exported.
    # This may require a pre-processing or manual checking to ensure that
    # your structs of interest all have the same names.
    mask = struct_to_mask(dicom_series_path, dicom_files, struct_name)
    if not np.any(mask):
        raise Exception(f'Struct with name {struct_name} was not found in {dicom_series_path}'
                        ' or did not contain any delineation data.'
                        'Are you sure that all structs of interest are named '
                        'consistently and non-empty?')
    return mask

def convert_fraction_to_nifty(in_dir, out_dir, struct_name):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    for image_type in ImageType:
        out_path = os.path.join(out_dir, f'{image_type}.nii.gz')
        if not os.path.isfile(out_path):

            if image_type == ImageType.SCAN:
                numpy_image = get_scan_image(in_dir)
            elif image_type == ImageType.DOSE:
                numpy_image = get_dose_image(in_dir)
            elif image_type == ImageType.STRUCT:
                numpy_image = get_struct_image(in_dir, struct_name)
            else:
                raise Exception(f'Unhandled {image_type}')
            logging.info(f'saving {image_type} to {out_path}')
            img = nib.Nifti1Image(numpy_image, np.eye(4))
            img.to_filename(out_path)


def multi_process(func, in_paths, out_paths, struct_name, cpus=os.cpu_count()):
    print('calling', func.__name__, 'on', len(in_paths), 'items')
    start = time.time()
    with Pool(cpus) as pool:
        async_results = []
        for in_path, out_path in zip(in_paths, out_paths):
            res = pool.apply_async(func, args=[in_path, out_path, struct_name])
            async_results.append(res)
        pool.close()
        pool.join()
        results = [res.get() for res in async_results]
        print(func.__name__, 'on', len(in_paths), 'items took', time.time() - start)
        return results


def convert_all_patients_to_nifty(in_dir, out_dir, struct_name, use_multi_process=True):
    # if the output folder does not exist then create it
    if not os.path.isdir(out_dir):
        logging.info(f'creating output directory for exported patient data {out_dir}')
        os.makedirs(out_dir)
    patient_dirs = os.listdir(in_dir)

    logging.info(f"found {len(patient_dirs)} patient directories")
    input_paths = []
    output_paths = []

    for patient_dir in patient_dirs:
        logging.info(f'processing {patient_dir}')
        patient_path = os.path.join(in_dir, patient_dir)
        fraction_dirs = os.listdir(patient_path)

        for fraction_dir in fraction_dirs:
            fraction_path = os.path.join(in_dir, patient_dir, fraction_dir)
            logging.info(f'processing {fraction_path}')
            output_path = os.path.join(out_dir, patient_dir, fraction_dir)
            input_paths.append(fraction_path)
            output_paths.append(output_path)

    assert input_paths, f'Could not find suitable input paths in {in_dir}'

    if use_multi_process:
        for fraction_path, output_path in zip(input_paths, output_paths):
            multi_process(convert_fraction_to_nifty, input_paths,
                          output_paths, struct_name)
    else:
        # single process
        for fraction_path, output_path in zip(input_paths, output_paths):
            convert_fraction_to_nifty(fraction_path, output_path, struct_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description="Dicom conversion utility. Convert from dicom to nifty",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", help="Directory containing patient folders")
    parser.add_argument("output", help="Output location for nifty files")
    parser.add_argument("-m", "--multi-process", action="store_true",
                        default=True, help="use multiprocessing")
    parser.add_argument("-s", "--struct-name", action="store_true",
                        default=True, help="name of structure")
    args = parser.parse_args()
    config = vars(args)
    sys.exit()
    convert_all_patients_to_nifty(config['input'], config['output'], config['stuct_name'],
                                  config['multi_process'])
