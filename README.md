# Retinal Image Viewer

## Overview

The Retinal Image Viewer is a web-based application designed for viewing and analyzing retinal images from various file formats, including DICOM, E2E, and FDS. It provides a user-friendly interface for medical professionals and researchers to examine retinal scans, extract metadata, and perform basic image processing tasks.

**Note:** We are planning to migrate to React.js in our next iteration to enhance the user interface and improve overall performance.

## Current Stack

- Backend: Python with FastAPI
- Frontend: HTML, CSS, and vanilla JavaScript
- Image Processing: PyDICOM, NumPy, SciPy, Pillow
- File Conversion: OCT-Converter

## Features

- Upload and view retinal images from DICOM, E2E, and FDS file formats
- Display individual frames from multi-frame images
- Extract and display image metadata
- Convert E2E files to DICOM format
- Download processed images and metadata in various formats (PNG, NPY, MAT)
- Apply windowing (contrast adjustment) to DICOM images
- Extract 2D and 3D pixel arrays from DICOM files

## Azure DevOps Pipeline

This project is set up with an Azure DevOps pipeline for continuous integration and deployment. The pipeline automates the following processes:

1. Code checkout from the repository
2. Environment setup and dependency installation
3. Running automated tests
4. Building the application
5. Deploying to staging/production environments

To view or modify the pipeline configuration, please refer to the `azure-pipelines.yml` file in the root of the repository.

## Development Setup

1. Clone the repository:
   ```
   git clone https://dev.azure.com/your-organization/your-project/_git/retinal-image-viewer
   cd retinal-image-viewer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application Locally

1. Start the backend server:
   ```
   python src/backend/main.py
   ```

2. Open a web browser and navigate to `http://127.0.0.1:8000/static/index.html` if the backend does not run automatically.

## API Endpoints

The application provides several API endpoints for processing retinal images. For detailed information on how to use these endpoints, please refer to the API documentation in the `docs` folder.

## Testing

To run the automated tests locally:

```
pytest tests/
```

## Deployment

Deployment is handled automatically by the Azure DevOps pipeline. For manual deployment instructions, please refer to the `deployment_guide.md` in the `docs` folder.

## License

[Include license information here]

## Contact

For questions or support, please contact the development team through the Azure DevOps project page.