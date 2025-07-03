# dicom_tool/converter.py

import os
import shutil
import signal
from oct_converter.dicom import create_dicom_from_oct
from oct_converter.readers import E2E
import argparse

# Global flag for interruption
interrupted = False

def signal_handler(signum, frame):
    global interrupted
    interrupted = True
    print("\nInterruption received. Cleaning up...")

# Set up the signal handler
signal.signal(signal.SIGINT, signal_handler)

def convert_e2e_to_dcm(file_path: str, output_dir: str):
    global interrupted
    print(f"Processing file: {file_path}")
    dcm_files = []
    
    try:
        # Ensure the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create output directory for this file
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        file_output_dir = os.path.join(output_dir, f"{file_name}_output")
        os.makedirs(file_output_dir, exist_ok=True)

        # Process the file (E2E to DICOM conversion)
        e2e = E2E(file_path)
        
        # Call create_dicom_from_oct with the file path, not the E2E object
        dcm_files = create_dicom_from_oct(file_path)

        # Ensure DICOM files were created
        if not dcm_files:
            raise Exception("Failed to convert the E2E file to DICOM.")
        
        # Move DICOM files to the output directory
        for dcm_file in dcm_files:
            if interrupted:
                print("Interruption detected. Stopping file moving.")
                return []
            dest_path = os.path.join(file_output_dir, os.path.basename(dcm_file))
            shutil.move(dcm_file, dest_path)
            print(f"Moved DICOM file to: {dest_path}")

        return dcm_files

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Error traceback: {traceback.format_exc()}")
        return []

def process_file(file_path, output_dir, verbose):
    if file_path.lower().endswith('.e2e'):
        try:
            convert_e2e_to_dcm(file_path, output_dir)
            return True
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return False
    else:
        print(f"Skipping {file_path}: Not an .e2e file")
        return False

def process_input(input_path, output_base_dir, verbose=False):
    # Get the name of the input folder or file
    input_name = os.path.basename(os.path.normpath(input_path))
    converter_output_dir = os.path.join(output_base_dir, "converter_output")
    final_output_dir = os.path.join(converter_output_dir, f"{input_name}_converted")
    
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
                    if item_path.lower().endswith('.e2e'):
                        error_files += 1
                    else:
                        skipped_files += 1
            
            elif os.path.isdir(item_path):
                process_directory(item_path, relative_item_path)

    if os.path.isfile(input_path):
        total_files = 1
        if process_file(input_path, final_output_dir, verbose):
            processed_files += 1
        else:
            if input_path.lower().endswith('.e2e'):
                error_files += 1
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
    parser = argparse.ArgumentParser(description="Convert E2E file(s) to DICOM.")
    parser.add_argument('input_path', type=str, help="Path to the E2E file or folder containing E2E files")
    parser.add_argument('-o', '--output', type=str, default=".", help="Path to the parent output directory")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    args = parser.parse_args()

    process_input(args.input_path, args.output, args.verbose)