import os
import cv2
import numpy as np
import random
from tqdm import tqdm
from pathlib import Path
import logging

# Default parameters - EDIT THESE PATHS before running
INPUT_DIR = r"C:\GONZALES\dataset_violencia\dataset_V2\videos_procesados\violence"  # Directory containing your videos
OUTPUT_DIR = r"C:\GONZALES\dataset_violencia\dataset_violence_fisica\frames_yolo"  # Directory where frames will be saved
FRAMES_PER_VIDEO = 3  # Number of frames to extract per video
TARGET_SIZE = 640  # Target size (width & height) for frames

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("frame_extraction.log")
        ]
    )
    return logging.getLogger("frame_extractor")

def create_directory(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def resize_with_padding(image, target_size):
    """
    Resize image to target size while maintaining aspect ratio and adding padding.
    
    Args:
        image: Input image (numpy array)
        target_size: Tuple (width, height) for target size
    
    Returns:
        Resized image with padding
    """
    h, w = image.shape[:2]
    target_w, target_h = target_size
    
    # Calculate scaling factor to maintain aspect ratio
    scale = min(target_w / w, target_h / h)
    
    # Calculate new dimensions
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Resize image while maintaining aspect ratio
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # Create a black image with target dimensions
    padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    
    # Calculate padding
    pad_x = (target_w - new_w) // 2
    pad_y = (target_h - new_h) // 2
    
    # Place resized image in center of padded image
    padded[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = resized
    
    return padded

def extract_frames(video_path, output_dir, num_frames=4, target_size=(640, 640), prefix=None):
    """
    Extract frames from a video and resize them to the target size.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory where frames will be saved
        num_frames: Number of frames to extract from the video
        target_size: Target size for the output frames
        prefix: Optional prefix for the output filename
    
    Returns:
        List of saved frame paths
    """
    try:
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return []
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        # Handle videos with very few frames
        if total_frames <= num_frames:
            # Just extract every frame
            frame_indices = list(range(total_frames))
        else:
            # Distribute frames evenly throughout the video
            frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
        
        # Generate filename prefix
        if prefix is None:
            prefix = os.path.splitext(os.path.basename(video_path))[0]
        
        saved_frames = []
        
        # Extract frames at calculated positions
        for idx, frame_pos in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            
            if not ret:
                logger.warning(f"Failed to read frame {frame_pos} from {video_path}")
                continue
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize frame with padding to maintain aspect ratio
            resized_frame = resize_with_padding(frame_rgb, target_size)
            
            # Convert back to BGR for saving with OpenCV
            resized_frame_bgr = cv2.cvtColor(resized_frame, cv2.COLOR_RGB2BGR)
            
            # Save frame
            frame_filename = f"{prefix}_frame_{idx:03d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            cv2.imwrite(frame_path, resized_frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            saved_frames.append(frame_path)
            
        cap.release()
        return saved_frames
        
    except Exception as e:
        logger.error(f"Error processing {video_path}: {str(e)}")
        return []

def process_videos(input_dir, output_dir, frames_per_video=4, target_size=(640, 640)):
    """
    Process all videos in the input directory and extract frames.
    
    Args:
        input_dir: Directory containing video files
        output_dir: Directory where frames will be saved
        frames_per_video: Number of frames to extract per video
        target_size: Target size for the output frames
    """
    # Create output directory if it doesn't exist
    create_directory(output_dir)
    
    # Find all video files
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(list(Path(input_dir).glob(f"**/*{ext}")))
    
    logger.info(f"Found {len(video_files)} videos to process")
    
    # Process each video
    total_frames_extracted = 0
    failed_videos = 0
    
    for video_path in tqdm(video_files, desc="Processing videos"):
        # Create a unique prefix for the frames from this video
        prefix = f"{video_path.stem}"
        
        # Extract frames
        saved_frames = extract_frames(
            str(video_path),
            output_dir,
            num_frames=frames_per_video,
            target_size=target_size,
            prefix=prefix
        )
        
        # Update statistics
        if saved_frames:
            total_frames_extracted += len(saved_frames)
        else:
            failed_videos += 1
    
    # Log summary
    logger.info(f"Extraction complete:")
    logger.info(f"- Total videos processed: {len(video_files)}")
    logger.info(f"- Total frames extracted: {total_frames_extracted}")
    logger.info(f"- Failed videos: {failed_videos}")
    logger.info(f"- Frames saved to: {output_dir}")

if __name__ == "__main__":
    # Set up logging
    logger = setup_logging()
    
    # Run the frame extraction process with the default parameters
    process_videos(
        INPUT_DIR,
        OUTPUT_DIR,
        frames_per_video=FRAMES_PER_VIDEO,
        target_size=(TARGET_SIZE, TARGET_SIZE)
    )
    
    print(f"\nFrame extraction complete!")
    print(f"Extracted {FRAMES_PER_VIDEO} frames per video from {INPUT_DIR}")
    print(f"Frames saved to: {OUTPUT_DIR}")