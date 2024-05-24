# Medical Image Coregistration

This project performs coregistration of medical images using FSL's FLIRT tool, Python's Nilearn library, and the Insight Segmentation and Registration Toolkit (ITK).

## Features

- Coregister medical images using FSL's FLIRT.
- Coregister images using Python's Nilearn library.
- Utilize ITK for image processing.
- Command-line interface for flexibility and ease of use.

## Requirements

- Python 3.x
- FSL (FMRIB Software Library)
- nibabel
- nilearn
- numpy
- argparse
- itk

## Installation

First, install the required Python packages:

```sh
pip install nibabel nilearn numpy argparse itk
```

Ensure FSL is installed and properly configured on your system. You can download FSL from [here](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation).

## Usage

Run the script from the command line:

```sh
python coregistration_cli.py /path/to/your/root_directory
```

Replace `/path/to/your/root_directory` with the actual path to the root directory containing `nifti`, `temp`, and `output` folders.

### Example Directory Structure

Your root directory should look like this:
```
/path/to/your/root_directory
├── nifti
│   ├── MPRAGE.nii.gz
│   └── MPRAGE_FSGAD.nii.gz
├── temp
│   ├── template.nii.gz
│   ├── mask_brain.nii.gz
│   └── atlas.nii.gz
└── output
```

### Notes

- Ensure that FSL is correctly installed and configured.
- Verify the availability of the necessary images in the specified directories.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
