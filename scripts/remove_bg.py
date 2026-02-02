from PIL import Image
import sys
import os
import numpy as np

def remove_black_background(image_path, output_path, threshold=30):
    try:
        print(f"Processing {image_path}...")
        img = Image.open(image_path).convert("RGBA")
        data = np.array(img)
        
        # Calculate max brightness of RGB channels
        max_channels = np.max(data[:, :, :3], axis=2)
        
        # Create alpha channel based on brightness
        # Pixels darker than threshold become transparent
        # Smooth transition for anti-aliasing effect
        alpha = np.copy(data[:, :, 3])
        
        # Simple aggressive masking for pure black background
        mask_black = max_channels < threshold
        data[mask_black, 3] = 0
        
        # Create new image
        new_img = Image.fromarray(data)
        new_img.save(output_path, "PNG")
        print(f"Saved to {output_path}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python remove_bg.py <input> <output>")
    else:
        remove_black_background(sys.argv[1], sys.argv[2])
