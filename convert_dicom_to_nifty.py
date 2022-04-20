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
import nibabel as nib
import time
from multiprocessing import Pool

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


def convert_scan_to_nifty(in_dir, out_dir, verbose):

    if verbose:
        print('convert scan to nifty. input fraction path', in_dir, 'output fraction path', out_dir)     

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)


    out_path = os.path.join(out_dir, 'scan.nii.gz')
    if not os.path.isfile(out_path):
        numpy_image = get_3d_image(in_dir)

        if verbose:
            print('saving scan to', out_path)
        img = nib.Nifti1Image(numpy_image, np.eye(4))
        img.to_filename(out_path)


def convert_dose_to_nifty(in_dir, out_dir, verbose):
    if verbose:
        print('convert dose to nifty. input fraction path', in_dir, 'output fraction path', out_dir)     
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    out_path = os.path.join(out_dir, 'dose.nii.gz')
    if not os.path.isfile(out_path):
        numpy_image = get_dose_image(in_dir)

        if verbose:
            print('saving dose to', out_path)
        img = nib.Nifti1Image(numpy_image, np.eye(4))
        img.to_filename(out_path)


def multi_process(func, in_paths, out_paths, verbose, cpus=os.cpu_count()):
    print('calling', func.__name__, 'on', len(in_paths), 'items')
    start = time.time()
    pool = Pool(cpus)
    async_results = []
    for in_path, out_path in zip(in_paths, out_paths):
        res = pool.apply_async(func, args=[in_path, out_path, verbose])
        async_results.append(res)
    pool.close()
    pool.join()
    results = [res.get() for res in async_results]
    print(func.__name__, 'on', len(in_paths), 'items took', time.time() - start)
    return results


def convert_to_nifty(in_dir, out_dir, verbose=False, use_multi_process=True):
    # if the output folder does not exist then create it
    if not os.path.isdir(out_dir):
        if verbose:
            print('creating output directory for exported patient data', out_dir)
        os.makedirs(out_dir)
    patient_dirs = os.listdir(in_dir)
    if verbose:
        print(f"found {len(patient_dirs)} patient directories")

    input_paths = []
    output_paths = []

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
            input_paths.append(fraction_path)
            output_paths.append(output_path)

    if input_paths:
        if use_multi_process:
            multi_process(convert_scan_to_nifty, input_paths, output_paths, verbose)
            multi_process(convert_dose_to_nifty, input_paths, output_paths, verbose)
        else:
            # single process
            for fraction_path, output_path in zip(input_paths, output_paths):
                convert_scan_to_nifty(fraction_path, output_path, verbose)
                convert_dose_to_nifty(fraction_path, output_path, verbose)
    else:
        print('Could not find suitable input paths in', in_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dicom conversion utility. Convert from dicom to nifty",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", help="Directory containing patient folders")
    parser.add_argument("output", help="Output location for nifty files")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")
    args = parser.parse_args()
    config = vars(args)
    convert_to_nifty(config['input'], config['output'], config['verbose'], use_multi_process=True)
