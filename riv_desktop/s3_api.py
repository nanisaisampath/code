from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import boto3
from pathlib import Path
import tempfile
import uuid
import os
import logging
import time
import zlib
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("s3_logger")

# Load .env from current directory
load_dotenv(Path(".env"))

router = APIRouter()

def env_credentials_present():
    return all([
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("AWS_DEFAULT_REGION"),
        os.getenv("AWS_S3_BUCKET"),
    ])

def save_credentials_to_env(credentials):
    """Save credentials to .env file"""
    try:
        env_path = Path(".env")
        
        # Read existing .env content
        existing_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_content = f.read()
        
        # Prepare new credentials
        new_lines = [
            f"AWS_ACCESS_KEY_ID={credentials['access_key']}",
            f"AWS_SECRET_ACCESS_KEY={credentials['secret_key']}",
            f"AWS_DEFAULT_REGION={credentials['region']}",
            f"AWS_S3_BUCKET={credentials['bucket']}"
        ]
        
        # Remove existing AWS credentials if present
        lines = existing_content.split('\n')
        filtered_lines = [line for line in lines if not any(
            line.startswith(key) for key in ['AWS_ACCESS_KEY_ID=', 'AWS_SECRET_ACCESS_KEY=', 'AWS_DEFAULT_REGION=', 'AWS_S3_BUCKET=']
        )]
        
        # Add new credentials
        filtered_lines.extend(new_lines)
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.write('\n'.join(line for line in filtered_lines if line.strip()))
            f.write('\n')
        
        logger.info(f"Credentials saved to {env_path}")
        return True
        
    except Exception as e:
        logger.error(f"Could not save to .env file: {str(e)}")
        return False

def calculate_s3_object_crc(s3_client, bucket: str, key: str) -> str:
    """Calculate CRC32 for an S3 object without downloading the entire file."""
    try:
        # For large files, we'll use the ETag as a proxy for CRC
        # For small files, we can download and calculate actual CRC
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        # Get file size
        file_size = response.get('ContentLength', 0)
        
        if file_size < 10 * 1024 * 1024:  # Less than 10MB, calculate actual CRC
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            content = obj['Body'].read()
            crc = zlib.crc32(content) & 0xFFFFFFFF
            return format(crc, '08x')
        else:
            # For larger files, use ETag + metadata as CRC proxy
            etag = response.get('ETag', '').strip('"')
            last_modified = response.get('LastModified', '').isoformat() if response.get('LastModified') else ''
            
            # Create a composite CRC from metadata
            metadata_str = f"{key}:{etag}:{last_modified}:{file_size}"
            crc = zlib.crc32(metadata_str.encode('utf-8')) & 0xFFFFFFFF
            return format(crc, '08x')
            
    except Exception as e:
        logger.warning(f"Could not calculate CRC for {key}: {str(e)}")
        # Fallback to path-based CRC
        crc = zlib.crc32(key.encode('utf-8')) & 0xFFFFFFFF
        return format(crc, '08x')

# Initialize S3 variables
s3 = None
bucket_name = None

if env_credentials_present():
    print("[S3 INIT] Using credentials from .env")
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION")
        )
        bucket_name = os.getenv("AWS_S3_BUCKET")
        print(f"[S3 INIT] Connected to bucket: {bucket_name}")
    except Exception as e:
        print(f"[S3 INIT] Error initializing S3: {e}")
        s3 = None
        bucket_name = None
else:
    print("[S3 INIT] .env credentials not found — will show web form")

@router.get("/api/s3-status")
async def get_s3_status():
    """Check if S3 is configured and accessible"""
    global s3, bucket_name
    
    if not s3 or not bucket_name:
        return {
            "configured": False,
            "needs_credentials": True,
            "message": "S3 credentials not configured"
        }
    
    try:
        # Test connection by checking if the specific bucket exists and is accessible
        s3.head_bucket(Bucket=bucket_name)
        return {
            "configured": True,
            "needs_credentials": False,
            "bucket": bucket_name,
            "message": "S3 configured and accessible"
        }
    except Exception as e:
        return {
            "configured": False,
            "needs_credentials": True,
            "error": str(e),
            "message": "S3 configured but not accessible"
        }

@router.post("/api/set-s3-credentials")
async def set_s3_credentials(request: Request):
    """Set S3 credentials from the frontend form"""
    global s3, bucket_name
    
    try:
        data = await request.json()
        access_key = data.get('accessKey')
        secret_key = data.get('secretKey')
        region = data.get('region')
        bucket = data.get('bucket')
        save_to_env = data.get('saveToEnv', False)
        
        if not all([access_key, secret_key, region, bucket]):
            raise HTTPException(status_code=400, detail="All fields are required")
        
        # Test the credentials
        test_s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Test connection
        test_s3.head_bucket(Bucket=bucket)
        
        # If successful, update global variables
        s3 = test_s3
        bucket_name = bucket
        
        response_data = {
            "message": "S3 credentials set successfully",
            "bucket": bucket,
            "region": region
        }
        
        # Save to .env if requested
        if save_to_env:
            credentials = {
                'access_key': access_key,
                'secret_key': secret_key,
                'region': region,
                'bucket': bucket
            }
            if save_credentials_to_env(credentials):
                response_data["saved_to_env"] = True
            else:
                response_data["saved_to_env"] = False
                response_data["env_warning"] = "Could not save to .env file"
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error setting S3 credentials: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid credentials or bucket: {str(e)}")


@router.get("/api/s3-flat-list")
async def get_s3_flat_list():
    global s3, bucket_name

    if not s3 or not bucket_name:
        return JSONResponse(
            status_code=503,
            content={
                "error": "S3 not configured. Please set credentials first.",
                "needs_credentials": True
            }
        )

    try:
        paginator = s3.get_paginator("list_objects_v2")
        files = []

        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.lower().endswith((".dcm", ".e2e", ".fds", ".dicom",".fda")):
                    continue

                files.append({
                    "key": key,
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat()
                })

        logger.info(f"S3 flat list loaded with {len(files)} items")
        return files

    except Exception as e:
        logger.error(f"Error loading S3 flat list: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/api/download_dicom_from_s3")
async def download_dicom_from_s3(path: str = Query(...)):
    global s3, bucket_name

    if not s3 or not bucket_name:
        return JSONResponse(
            status_code=503,
            content={
                "error": "S3 not configured. Please set credentials first.",
                "needs_credentials": True
            }
        )

    try:
        from main import process_dicom_file, process_e2e_file, process_fds_file,process_fda_file, stored_images
    except ImportError:
        logger.error("Could not import processing functions from main")
        raise HTTPException(status_code=500, detail="Server configuration error")

    # Generate CRC for this file path and metadata
    try:
        # Get S3 object metadata for CRC calculation
        head_response = s3.head_object(Bucket=bucket_name, Key=path)
        file_size = head_response.get('ContentLength', 0)
        last_modified = head_response.get('LastModified', '').isoformat() if head_response.get('LastModified') else ''
        etag = head_response.get('ETag', '').strip('"')
        
        # Calculate CRC based on file metadata
        metadata_str = f"{path}:{etag}:{last_modified}:{file_size}"
        crc = format(zlib.crc32(metadata_str.encode('utf-8')) & 0xFFFFFFFF, '08x')
        
        logger.info(f"Generated CRC for {path}: {crc}")
        
    except Exception as e:
        logger.warning(f"Could not get S3 metadata for {path}: {str(e)}")
        # Fallback CRC based on path only
        crc = format(zlib.crc32(path.encode('utf-8')) & 0xFFFFFFFF, '08x')

    cache_key = path.replace('/', '_').replace('.', '_')

    # Return cached version if present (check both memory and CRC)
    for key, value in stored_images.items():
        if isinstance(value, dict) and (
            value.get("s3_key") == path or 
            value.get("crc") == crc
        ):
            logger.info(f"Cache hit for {path} (CRC: {crc})")
            return JSONResponse(content={
                "message": "File loaded from memory cache.",
                "number_of_frames": len([k for k in value.keys() if isinstance(k, int)]),
                "dicom_file_path": key,
                "cache_source": "memory"
            })

    file_extension = os.path.splitext(path)[1].lower()
    key = str(uuid.uuid4())

    logger.info(f"Downloading {path} from S3 into memory")
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=path)
        file_bytes = obj['Body'].read()  # Read the full content into memory
    except Exception as e:
        logger.error(f"Failed to get S3 object: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Failed to download file: {str(e)}")

    import io
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        tmp.write(file_bytes)
        temp_path = tmp.name

    logger.info(f"Downloaded and saved to temp file: {temp_path}")

    stored_images[key] = {
        "local_path": temp_path,
        "s3_key": path,
        "timestamp": time.time(),
        "crc": crc
    }

    try:
        if file_extension in ['.dcm', '.dicom']:
            return process_dicom_file(temp_path, key, crc)
        elif file_extension == '.e2e':
            return process_e2e_file(temp_path, key, crc)
        elif file_extension in ['.fds']:
            return process_fds_file(temp_path, key, crc)
        elif file_extension in ['.fda']:
            return process_fda_file(temp_path, key, crc)
        else:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Processing error for {path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Enhanced endpoint to get S3 object CRC
@router.get("/api/s3-object-crc")
async def get_s3_object_crc(path: str = Query(...)):
    """Get CRC checksum for an S3 object."""
    global s3, bucket_name
    
    if not s3 or not bucket_name:
        raise HTTPException(status_code=503, detail="S3 not configured")
    
    try:
        crc = calculate_s3_object_crc(s3, bucket_name, path)
        logger.info(f"Calculated CRC for S3 object {path}: {crc}")
        
        return {
            "path": path,
            "crc": crc,
            "source": "s3_metadata"
        }
        
    except Exception as e:
        logger.error(f"Error calculating CRC for S3 object {path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating CRC: {str(e)}")