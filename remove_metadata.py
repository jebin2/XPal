import os
import subprocess
from PIL import Image
from PIL.ExifTags import TAGS
from pathlib import Path

def remove_image_metadata(image_path, output_path):
    try:
        with Image.open(image_path) as img:
            # Get original format and mode
            original_format = img.format
            original_mode = img.mode
            
            # Create a new image without metadata
            # This preserves the original mode and format when possible
            if hasattr(img, '_getexif') and img._getexif():
                print(f"[i] Found EXIF data in {os.path.basename(image_path)}")
            
            # For PNG with transparency, preserve it
            if original_format == 'PNG' and original_mode in ('RGBA', 'LA', 'P'):
                # Keep original format and transparency
                clean_img = Image.new(original_mode, img.size)
                if original_mode == 'P':
                    clean_img.putpalette(img.getpalette())
                clean_img.paste(img, (0, 0))
                clean_img.save(output_path, format='PNG', optimize=True)
            
            # For JPEG or when converting to JPEG
            elif original_format == 'JPEG' or output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                # Convert to RGB if necessary, but preserve quality
                if original_mode != 'RGB':
                    clean_img = img.convert('RGB')
                else:
                    clean_img = img.copy()
                clean_img.save(output_path, format='JPEG', quality=100, optimize=True, 
                             progressive=True, exif=b'')  # Explicitly remove EXIF
            
            # For other formats, try to preserve original format
            else:
                clean_img = img.copy()
                # Remove all metadata by creating new image
                new_img = Image.new(img.mode, img.size)
                new_img.paste(clean_img)
                new_img.save(output_path, format=original_format, optimize=True)
                
        print(f"[✓] Cleaned image saved: {output_path}")
        
        # Verify metadata removal
        verify_image_metadata_removal(output_path)
        
    except Exception as e:
        print(f"[!] Failed to clean image: {e}")

def verify_image_metadata_removal(image_path):
    """Verify that metadata has been successfully removed"""
    try:
        with Image.open(image_path) as img:
            # Check for EXIF data
            exif_data = img._getexif()
            if exif_data:
                print(f"[!] Warning: Some EXIF data still present in {os.path.basename(image_path)}")
                return False
            else:
                print(f"[✓] No EXIF data found in cleaned image")
                return True
    except:
        print(f"[✓] No EXIF data found in cleaned image")
        return True

def remove_video_metadata(video_path, output_path):
    try:
        # Enhanced ffmpeg command with more thorough metadata removal
        cmd = [
            "ffmpeg", "-i", video_path,
            # Remove all metadata streams and tags
            "-map_metadata", "-1",
            "-map_chapters", "-1",
            # Remove specific metadata fields
            "-metadata", "title=",
            "-metadata", "author=", 
            "-metadata", "album=",
            "-metadata", "date=",
            "-metadata", "comment=",
            "-metadata", "genre=",
            "-metadata", "composer=",
            "-metadata", "performer=",
            "-metadata", "copyright=",
            "-metadata", "encoded_by=",
            "-metadata", "encoder=",
            "-metadata", "creation_time=",
            # Video encoding settings for high quality
            "-c:v", "libx264",
            "-crf", "18",  # High quality (lower = better quality)
            "-preset", "slow",  # Better compression
            "-profile:v", "high",
            "-level", "4.1",
            # Audio encoding settings
            "-c:a", "aac",
            "-b:a", "320k",  # High quality audio
            "-ac", "2",  # Stereo
            # Output settings
            "-movflags", "+faststart",  # Web optimization
            "-pix_fmt", "yuv420p",  # Compatibility
            "-avoid_negative_ts", "make_zero",  # Avoid timestamp issues
            "-fflags", "+genpts",  # Generate presentation timestamps
            "-y", output_path  # Overwrite output file
        ]
        
        print(f"[i] Processing video: {os.path.basename(video_path)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[✓] Cleaned video saved: {output_path}")
            verify_video_metadata_removal(output_path)
        else:
            print(f"[!] FFmpeg error: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to clean video: {e}")
    except FileNotFoundError:
        print("[!] Error: FFmpeg not found. Please install FFmpeg first.")

def verify_video_metadata_removal(video_path):
    """Verify that video metadata has been removed"""
    try:
        cmd = ["ffprobe", "-v", "quiet", "-show_format", "-show_streams", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if "TAG:" in result.stdout:
            print(f"[!] Warning: Some metadata tags might still be present")
        else:
            print(f"[✓] Video metadata successfully removed")
            
    except:
        print("[i] Could not verify metadata removal (ffprobe not available)")

def clean_media_file(input_path):
    """
    Clean metadata from media files
    
    Args:
        input_path: Path to the input file
        preserve_format: If True, try to keep original format. If False, convert images to JPEG
    """
    if not os.path.exists(input_path):
        print(f"[!] File not found: {input_path}")
        return
    
    filename, ext = os.path.splitext(input_path)
    ext = ext.lower()
    temp_path = "tempOutput"
    Path(temp_path).mkdir(parents=True, exist_ok=True)
    output_path = f"{temp_path}/{filename}_clean{ext}"

    print(f"[i] Input: {os.path.basename(input_path)}")
    print(f"[i] Output: {os.path.basename(output_path)}")
    
    # Process based on file type
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
        remove_image_metadata(input_path, output_path)
    elif ext in [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"]:
        remove_video_metadata(input_path, output_path)
    else:
        print(f"[!] Unsupported file format: {ext}")
        return input_path
    
    # Show file size comparison
    if os.path.exists(output_path):
        original_size = os.path.getsize(input_path)
        cleaned_size = os.path.getsize(output_path)
        size_diff = ((cleaned_size - original_size) / original_size) * 100
        print(f"[i] Size change: {size_diff:+.1f}% ({original_size:,} → {cleaned_size:,} bytes)")

    return output_path

def batch_clean_directory(directory_path):
    """Clean all supported media files in a directory"""
    supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', 
                          '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']
    
    if not os.path.exists(directory_path):
        print(f"[!] Directory not found: {directory_path}")
        return
    
    files_processed = 0
    for filename in os.listdir(directory_path):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(directory_path, filename)
            print(f"\n--- Processing {filename} ---")
            clean_media_file(file_path)
            files_processed += 1
    
    print(f"\n[✓] Processed {files_processed} files")

# ===== Example usage =====
if __name__ == "__main__":
    # Single file processing
    file_path = "media/ChatGPT Image Jun 11, 2025, 09_35_19 AM.png"
    
    if os.path.exists(file_path):
        clean_media_file(file_path)
    else:
        print(f"[!] Example file not found: {file_path}")
        print("[i] Please update the file_path variable with your actual file path")
    
    # Batch processing example (uncomment to use)
    # batch_clean_directory("media/")