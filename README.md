# registration_extras

Python module to run ANTs registration.

## convert_dicom_to_nifty.py

### Input

Input folder full of dicom directories.
The dicom files contain the scan, structure set and dose.
These files are all in the same directory, but a unique directory for each patient fraction


### Processing

Converts RT struct, RT dose and the scan image for each patient fraction.
These are converted to Nifty (nii.gz) to work with the ANTS registration software.

### Command line usage

``
usage: convert_dicom_to_nifty.py [-h] [-v] input output

Dicom conversion utility. Convert from dicom to nifty

positional arguments:
  input          Directory containing patient folders
  output         Output location for nifty files

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  increase verbosity (default: False)
``





