import os
import json
import zipfile
import pydicom
import numpy as np
import scipy.io as sio
import signal
import argparse

# Global flag for interruption
interrupted = False

def signal_handler(signum, frame):
    global interrupted
    interrupted = True
    print("\nInterruption received. Cleaning up...")

# Set up the signal handler
signal.signal(signal.SIGINT, signal_handler)

def extract_all_dicom_metadata(dicom):
    metadata = {}
    for elem in dicom.iterall():
        if elem.tag != (0x7FE0, 0x0010):  # Exclude pixel data
            if elem.VR == "SQ":  # Handle sequences
                metadata[elem.name] = [extract_all_dicom_metadata(dataset) for dataset in elem.value]
            else:
                metadata[elem.name] = str(elem.value)  # Convert all values to strings
    return metadata

def process_dicom_file(file_path, output_dir):
    global interrupted
    print(f"Starting to process file: {file_path}")
    try:
        # Extract the file name without the extension
        original_file_name = os.path.splitext(os.path.basename(file_path))[0]
        print(f"Original file name: {original_file_name}")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return

    # Create output directory within extractor_output_dir
    output_dir = os.path.join(output_dir, f"{original_file_name}_output")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")

    try:
        # Read the DICOM file
        dicom = pydicom.dcmread(file_path)
        print("Successfully read DICOM file")
        
        pixel_array = dicom.pixel_array
        bits_per_pixel = dicom.BitsAllocated
        print(f"Pixel array shape: {pixel_array.shape}, Bits per pixel: {bits_per_pixel}")

        # Extract pixel spacing and slice thickness
        pixel_spacing = None
        slice_thickness = None
        
        if hasattr(dicom, 'SharedFunctionalGroupsSequence'):
            try:
                shared_group = dicom.SharedFunctionalGroupsSequence[0]
                pixel_measures_seq = shared_group.PixelMeasuresSequence[0]
                pixel_spacing = [float(val) for val in pixel_measures_seq.PixelSpacing]
                slice_thickness = float(pixel_measures_seq.SliceThickness)
            except Exception:
                pass

        if pixel_spacing is None:
            pixel_spacing = [float(val) for val in dicom.PixelSpacing] if 'PixelSpacing' in dicom else [1.0, 1.0]
        
        if slice_thickness is None:
            slice_thickness = float(dicom.SliceThickness) if 'SliceThickness' in dicom else 1.0

        # Shape of the 3D pixel array
        Z, Y, X = pixel_array.shape if len(pixel_array.shape) == 3 else (1, *pixel_array.shape)

        # Prepare metadata as JSON
        metadata = {
            "X": X,
            "Y": Y,
            "Z": Z,
            "bits_per_pixel": bits_per_pixel,
            "pixel_spacing_mm": pixel_spacing,
            "slice_thickness_mm": slice_thickness
        }

        # Prepare output file names
        json_file_name = os.path.join(output_dir, f"pixel_dim_{original_file_name}.json")
        npy_file_name = os.path.join(output_dir, f"raw_pixels_numpy_{original_file_name}.npy")
        mat_file_name = os.path.join(output_dir, f"raw_pixels_matlab_{original_file_name}.mat")
        full_metadata_json = os.path.join(output_dir, f"full_nonpixel_metadata_{original_file_name}.json")
        zip_file_name = os.path.join(output_dir, f"{original_file_name}_dicom_data.zip")

        # Write the pixel dimension JSON metadata
        with open(json_file_name, "w") as json_file:
            json.dump(metadata, json_file)

        # Save the pixel data in .npy
        np.save(npy_file_name, pixel_array)

        # Save the pixel data in .mat
        sio.savemat(mat_file_name, {"pixel_array": pixel_array})
        print(f"Saved pixel data to {mat_file_name}")

        # Extract and save full metadata
        full_metadata = extract_all_dicom_metadata(dicom)
        with open(full_metadata_json, "w") as json_file:
            json.dump(full_metadata, json_file, indent=2)
        print(f"Saved full metadata to {full_metadata_json}")

        # Create a zip file containing all output files
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if interrupted:
                        print("Interruption detected. Stopping zip creation.")
                        return
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    try:
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        print(f"Error adding {file_path} to zip: {str(e)}")

        print(f"Processing complete. Output saved in {zip_file_name}")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()  # This will print the full stack trace
    finally:
        if interrupted:
            print("Cleaning up incomplete zip file...")
            try:
                os.remove(zip_file_name)
            except:
                pass

def process_file(file_path, output_dir, verbose):
    try:
        # Try to read the file as a DICOM file
        dicom = pydicom.dcmread(file_path)
        process_dicom_file(file_path, output_dir)
        return True
    except pydicom.errors.InvalidDicomError:
        print(f"Skipping {file_path}: Not a valid DICOM file")
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def process_input(input_path, output_base_dir, verbose=False):
    # Get the name of the input folder or file
    input_name = os.path.basename(os.path.normpath(input_path))
    extractor_output_dir = os.path.join(output_base_dir, "extractor_output")
    final_output_dir = os.path.join(extractor_output_dir, f"{input_name}_extracted")
    
    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)
        print(f"Created output directory: {final_output_dir}")

    total_files = 0
    processed_files = 0
    skipped_files = 0
    error_files = 0

    def process_directory(current_path, relative_path=""):
        nonlocal total_files, processed_files, skipped_files, error_files
        
        for item in os.listdir(current_path):
            if interrupted:
                print("\nInterruption detected. Stopping folder processing.")
                return
            
            item_path = os.path.join(current_path, item)
            relative_item_path = os.path.join(relative_path, item)
            
            if os.path.isfile(item_path):
                total_files += 1
                output_dir = os.path.join(final_output_dir, os.path.dirname(relative_item_path))
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                print(f"\nProcessing file {total_files}: {relative_item_path}")
                if process_file(item_path, output_dir, verbose):
                    processed_files += 1
                else:
                    skipped_files += 1
            
            elif os.path.isdir(item_path):
                process_directory(item_path, relative_item_path)

    if os.path.isfile(input_path):
        total_files = 1
        if process_file(input_path, final_output_dir, verbose):
            processed_files += 1
        else:
            skipped_files += 1
    elif os.path.isdir(input_path):
        process_directory(input_path)
    else:
        print(f"Invalid input path: {input_path}")

    print(f"\nProcessing complete. Summary:")
    print(f"Total files: {total_files}")
    print(f"Processed files: {processed_files}")
    print(f"Skipped files: {skipped_files}")
    print(f"Errors: {error_files}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract data from DICOM file(s).")
    parser.add_argument('input_path', type=str, help="Path to the DICOM file or folder containing DICOM files")
    parser.add_argument('-o', '--output', type=str, default=".", help="Path to the parent output directory")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    args = parser.parse_args()

    process_input(args.input_path, args.output, args.verbose)
