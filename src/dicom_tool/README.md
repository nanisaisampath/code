# DICOM Tool

## Overview

This tool provides two Python scripts for working with DICOM (Digital Imaging and Communications in Medicine) and E2E (Heidelberg Engineering Raw Data) files:

1. `extractor.py`: Extracts metadata and pixel data from DICOM files

   This script creates four main output files:

   a. `raw_pixels_numpy_<original_filename>.npy`:
      - A NumPy array file containing the raw pixel data from the DICOM image.
      - Can be easily loaded into Python for further analysis or processing.
      - Preserves the original data type and shape of the pixel array.

   b. `raw_pixels_matlab_<original_filename>.mat`:
      - A MATLAB-compatible file containing the raw pixel data.
      - Allows for easy import into MATLAB for users who prefer that environment.
      - Stores the pixel data as a matrix, maintaining its original structure.

   c. `pixel_dim_<original_filename>.json`:
      - A JSON file containing key metadata about the pixel dimensions and basic DICOM information.
      - Includes details such as image dimensions (X, Y, Z), bits per pixel, and slice thickness.
      - Provides a quick reference for the image's basic properties without needing to parse the full DICOM data.

   d. `full_nonpixel_metadata_<original_filename>.json`:
      - A comprehensive JSON file containing all non-pixel DICOM metadata.
      - Includes detailed information about the study, series, equipment, and acquisition parameters.
      - Useful for in-depth analysis of the DICOM file's metadata without dealing with the large pixel data.

2. `converter.py`: Converts E2E files to DICOM format

## Requirements

- Python 3.6 or later
- Dependencies listed in `requirements.txt`

## Setup

1. Ensure you have Python 3.6 or later installed. You can check your Python version by running:
   ```python
   python --version
   ```

2. Open a terminal/command prompt in this directory.

3. It's recommended (but not required) to create a virtual environment:
   ```python
   python -m venv venv
   ```
   Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`

4. Install the required dependencies:
   ```python
   python -m pip install -r requirements.txt
   ```

## Usage

### Extracting DICOM metadata and pixel data:

```
python extractor.py path/to/your/dicom_file.dcm
```

This script will:
- Extract metadata from the DICOM file
- Save pixel data in both .npy (NumPy) and .mat (MATLAB) formats
- Create a JSON file with pixel dimensions and other metadata
- Generate a ZIP file containing all extracted data

Output files will be saved in a new directory named after the input file.

### Converting E2E to DICOM:

```
python converter.py path/to/your/e2e_file.e2e
```

This script will:
- Convert the E2E file to DICOM format
- Save the resulting DICOM file(s) in the same directory as the input E2E file

## Output

### Extractor Output

The extractor script creates a directory named `<original_filename>_output` containing:
- `raw_pixels_numpy_<original_filename>.npy`: Pixel data in NumPy format
- `raw_pixels_matlab_<original_filename>.mat`: Pixel data in MATLAB format
- `pixel_dim_<original_filename>.json`: JSON file with pixel dimensions and basic metadata
- `full_nonpixel_metadata_<original_filename>.json`: Complete DICOM metadata (excluding pixel data)

All these files are also compressed into a ZIP file named `<original_filename>_dicom_data.zip`.

### Converter Output

The converter script generates one or more DICOM files from the input E2E file. These are saved in the same directory as the input file, with names assigned by the conversion process.

## Troubleshooting

- If you encounter any "module not found" errors, ensure you've activated the virtual environment and installed all dependencies from `requirements.txt`.
- For issues with specific DICOM or E2E files, check that the files are not corrupted and are in the expected format.
- If the converter fails to process an E2E file, ensure you have the latest version of the `oct-converter` library installed.

## Notes

- This tool is designed for research and educational purposes. Always ensure you have the right to access and process any medical imaging data.
- DICOM files can be large. Ensure you have sufficient disk space for extracted data and converted files.
- Processing time may vary depending on the size and complexity of the input files.

For any issues, feature requests, or questions, please contact Julian Pennington at jpennington@kodiak.com. 

## Using as a Python Package

This tool can also be used as a Python package, allowing you to import its functions into your own Python scripts.

1. Ensure the `dicom_tool` directory is in your Python path or in your current working directory.

2. You can then import and use the functions like this:

   ```python
   from dicom_tool.extractor import process_dicom_file
   from dicom_tool.converter import convert_e2e_to_dcm

   # Extract data from a DICOM file
   process_dicom_file('path/to/your/dicom_file.dcm')

   # Convert an E2E file to DICOM
   convert_e2e_to_dcm('path/to/your/e2e_file.e2e')
   ```

3. The `__init__.py` file in the `dicom_tool` directory allows Python to treat the directory as a package, enabling these imports.

This approach allows for more flexible integration of the DICOM tool functionalities into larger Python projects or custom workflows.


## Contact Information

For questions, issues, or feature requests, please contact:

Julian G. Pennington
Email: jpennington@kodiak.com

## License

This project is licensed under the MIT License.

Copyright (c) 2024 Kodiak Sciences Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## Third-Party Licenses

This project uses several open-source libraries. Their respective licenses are listed below:

### pydicom

Copyright (c) 2008-2023 pydicom developers

Distributed under the MIT License. For full terms, see:
https://github.com/pydicom/pydicom/blob/master/LICENSE

### NumPy

Copyright (c) 2005-2023 NumPy Developers

Distributed under the BSD 3-Clause License. For full terms, see:
https://numpy.org/doc/stable/license.html

### SciPy

Copyright (c) 2001-2002 Enthought, Inc. 2003-2023, SciPy Developers

Distributed under the BSD 3-Clause License. For full terms, see:
https://github.com/scipy/scipy/blob/main/LICENSE.txt

### oct-converter

Copyright (c) 2020 Markus Mayer

Distributed under the MIT License. For full terms, see:
https://github.com/marksgraham/OCT-Converter/blob/master/LICENSE

These libraries are essential components of our DICOM Tool, and we are grateful to their developers and contributors for their work.

