# DART - Dose Accumulation Registration Toolkit


``` 

\\\\\\       ________       
 >>>>>>---==(________)------
//////

Hit the bullseye with your dose accumulation!

```

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

```
usage: convert_dicom_to_nifty.py [-h] [--multi-process | --no-multi-process] --struct-name STRUCTNAME input output

Dicom conversion utility. Convert from dicom to nifty

positional arguments:
  input                 Directory containing patient folders
  output                Output location for nifty files

optional arguments:
  -h, --help            show this help message and exit
  --multi-process, --no-multi-process
  --struct-name STRUCTNAME
                        name of structure (default: None)

```

## Road map

Note: 🚧 = Under construction (not yet implemented).

* Convet a folder of dicoms to niftys as this is required for ANTS to run. ✅
* * Scans ✅
* * Dose ✅
* * Structures ✅
* Compute ANTS registration (and generate transformed images) on the folder of nifty scans ✅
* Run computed ants registration on: 
* * Dose - To allow dose summation (giving hopefully more accurate dose to each organ) ✅
* * Structures - To allow evaluation of registration accuracy by computing resultant segmentation metrics such as dice or hd. ✅
* Sum dose - Performed on dose files and giving a resultant dose for each patient. ✅
* Compute metrics - Compute segment metrics on the original contour and transformed (registered) contours. ✅
* Compute jacobian - Another image which displays characteristics of the deformation field (did any local regions fold?) 🚧
* Compute MI - Mutual information - Could give an indication if the registration was performed successfully. 🚧



## Development tools

This module is only supported with >= python3.9

RADON is used for measurement of cyclomatic complexity and maintainability index.

To assess cylomatic complexity:
> radon cc file_path.py
We aim to ensure all functions are rated B or above

To assess maintainability index:
> radon mi file_path.py
We aim to ensure all files are rated B or above.

To use pylint to check for errors
> pylint file_path.py

