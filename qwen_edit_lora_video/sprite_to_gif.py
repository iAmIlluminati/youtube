"""
Sprite Sheet to GIF Converter

Takes all 2x2 sprite sheets from the output folder and converts them into animated GIFs.
Each sprite sheet is split into 4 frames (top-left, top-right, bottom-left, bottom-right)
and animated as a looping GIF.
"""

from pathlib import Path
from PIL import Image
import os


# Configuration
OUTPUT_DIR = Path(__file__).parent / "generated_images"
OUTPUT_SPRITES_DIR = OUTPUT_DIR / "output"
GIF_IMAGES_DIR = OUTPUT_DIR / "gif_images"

# GIF settings
GIF_DURATION = 200  # Duration per frame in milliseconds (200ms = 0.2 seconds)
GIF_LOOP = 0  # 0 = infinite loop


def split_sprite_sheet(image_path: Path) -> list[Image.Image]:
    """
    Split a 2x2 sprite sheet into 4 individual frames.
    Returns frames in order: top-left, top-right, bottom-left, bottom-right
    """
    img = Image.open(image_path)
    width, height = img.size
    
    # Calculate dimensions for each frame (2x2 grid)
    frame_width = width // 2
    frame_height = height // 2
    
    frames = []
    
    # Extract frames in order: top-left, top-right, bottom-left, bottom-right
    # (0, 0) -> top-left
    frames.append(img.crop((0, 0, frame_width, frame_height)))
    # (frame_width, 0) -> top-right
    frames.append(img.crop((frame_width, 0, width, frame_height)))
    # (0, frame_height) -> bottom-left
    frames.append(img.crop((0, frame_height, frame_width, height)))
    # (frame_width, frame_height) -> bottom-right
    frames.append(img.crop((frame_width, frame_height, width, height)))
    
    return frames


def create_gif_from_sprite_sheet(sprite_sheet_path: Path, output_gif_path: Path) -> bool:
    """
    Convert a 2x2 sprite sheet into an animated GIF.
    Returns True if successful, False otherwise.
    """
    try:
        # Split sprite sheet into frames
        frames = split_sprite_sheet(sprite_sheet_path)
        
        # Save as animated GIF
        frames[0].save(
            output_gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=GIF_DURATION,
            loop=GIF_LOOP,
            format='GIF'
        )
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating GIF: {e}")
        return False


def main():
    """
    Main entry point - converts all sprite sheets in output folder to GIFs
    """
    # Create GIF images directory
    GIF_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all PNG files from output folder
    sprite_sheets = list(OUTPUT_SPRITES_DIR.glob("*.png"))
    
    if not sprite_sheets:
        print("=" * 70)
        print("❌ No sprite sheets found in output folder!")
        print(f"📁 Looking in: {OUTPUT_SPRITES_DIR.absolute()}")
        print("=" * 70)
        return
    
    print("=" * 70)
    print("🎬 SPRITE SHEET TO GIF CONVERTER")
    print("=" * 70)
    print(f"📁 Input folder: {OUTPUT_SPRITES_DIR.absolute()}")
    print(f"📁 Output folder: {GIF_IMAGES_DIR.absolute()}")
    print(f"📊 Found {len(sprite_sheets)} sprite sheets")
    print(f"⏱️  Frame duration: {GIF_DURATION}ms")
    print("=" * 70)
    print()
    
    converted_count = 0
    skipped_count = 0
    
    for sprite_sheet_path in sprite_sheets:
        # Create output GIF filename (same name but .gif extension)
        gif_filename = sprite_sheet_path.stem + ".gif"
        gif_path = GIF_IMAGES_DIR / gif_filename
        
        print(f"🎞️  Converting: {sprite_sheet_path.name} -> {gif_filename}")
        
        if create_gif_from_sprite_sheet(sprite_sheet_path, gif_path):
            print(f"   ✅ Saved: {gif_filename}")
            converted_count += 1
        else:
            print(f"   ⏭️  Skipped: {sprite_sheet_path.name}")
            skipped_count += 1
    
    print()
    print("=" * 70)
    print("✨ CONVERSION COMPLETE!")
    print("=" * 70)
    print(f"✅ Converted: {converted_count}/{len(sprite_sheets)} sprite sheets")
    if skipped_count > 0:
        print(f"⏭️  Skipped: {skipped_count} sprite sheets")
    print(f"📁 GIFs saved to: {GIF_IMAGES_DIR.absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    main()

