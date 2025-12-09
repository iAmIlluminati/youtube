"""
Pixel Art Sprite Sheet Generator using Replicate's google/nano-banana-pro model

Two-pass generation:
1. First pass: Generate base pixel art character sprites (square, 1:1) -> saved to input/
2. Second pass: Generate 2x2 sprite sheets with actions using base sprites as reference -> saved to output/
"""

import os
import random
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict

import replicate


# Configuration
MODEL = "google/nano-banana-pro"
OUTPUT_DIR = Path(__file__).parent / "generated_images"
INPUT_DIR = OUTPUT_DIR / "input"
OUTPUT_SPRITES_DIR = OUTPUT_DIR / "output"
RESOLUTION = "1K"
OUTPUT_FORMAT = "png"

# Background colors for pixel art sprites (solid colors, no transparency)
BACKGROUND_COLORS = [
    "#1a1a2e",  # Dark navy
    "#16213e",  # Dark blue
    "#0f3460",  # Deep blue
    "#533483",  # Purple
    "#2d2d44",  # Dark gray-blue
    "#3d3d5c",  # Medium gray-blue
    "#4a4a6a",  # Lighter gray-blue
    "#2c3e50",  # Dark slate
    "#34495e",  # Medium slate
    "#1e1e2e",  # Very dark navy
    "#252525",  # Dark gray
    "#2a2a3e",  # Dark purple-gray
    "#1a1a3a",  # Dark indigo
    "#3a3a5a",  # Medium indigo
]

# Pixel art style suffix for base character generation (will include background color)
PIXEL_ART_BASE = "Pixel art style, 16-bit retro game sprite, clean pixels, solid colors, no blur, centered character on solid background, front-facing view, no transparency."

# Sprite sheet suffix for action generation (will include background color)
SPRITE_SHEET_BASE = "2x2 grid sprite sheet, pixel art style, 16-bit retro game sprite, 4 frames showing the action sequence in place, character stays centered in same position in all frames, no horizontal movement, clean pixels, solid colors, no blur, solid background, no transparency. Arrange frames in 2 rows and 2 columns: top-left (frame 1), top-right (frame 2), bottom-left (frame 3), bottom-right (frame 4). Frame 4 must loop smoothly back to frame 1 creating a seamless infinite animation cycle."

# Character prompts for base pixel art sprites
CHARACTER_PROMPTS = [
    # Original characters (commented out)
    # "Knight in silver armor holding a sword and shield",
    # "Wizard in purple robes with pointed hat and staff",
    # "Rogue in dark leather armor with dual daggers",
    # "Archer in green cloak with bow and quiver",
    # "Barbarian warrior with battle axe and fur clothing",
    # "Mage in blue robes with glowing orb",
    # "Paladin in golden armor with holy symbol",
    # "Ninja in black outfit with katana",
    # "Pirate with eyepatch, tricorn hat and cutlass",
    # "Samurai in traditional armor with katana",
    # "Viking with horned helmet and axe",
    # "Cyber warrior in futuristic armor with laser gun",
    # "Space marine in power armor with rifle",
    # "Robot character with mechanical limbs",
    # "Elf ranger with longbow and nature-themed clothing",
    # "Dwarf warrior with hammer and heavy armor",
    # "Alien character with tentacles and advanced technology",
    # "Steampunk inventor with goggles and mechanical gadgets",
    # "Monk in simple robes with staff",
    # "Necromancer in dark robes with skull staff",
    
    # New unique characters
    "Druid in nature robes with staff and animal companion",
    "Bard with lute and magical musical notes",
    "Cleric in white robes with holy symbol and healing light",
    "Assassin in shadow cloak with hidden blades",
    "Beastmaster with tamed wolf and hunting gear",
    "Alchemist with potion belt and glowing flasks",
    "Gunslinger with revolver and cowboy hat",
    "Shaman with totem staff and tribal feathers",
    "Demon hunter with crossbow and holy water vials",
    "Time traveler with futuristic chronometer and portal device",
    "Elemental mage with swirling fire and ice orbs",
    "Shadow assassin blending with darkness and dual katanas",
    "Crystal mage with floating glowing crystals",
    "Mech pilot in powered exosuit with plasma cannon",
    "Phoenix warrior with fire wings and flaming sword",
]

# Actions for sprite sheet generation
# Mix of simple/common actions and complex magical/transformative actions
ACTIONS = [
    # Simple/common actions
    "walking forward",
    "jumping up",
    "attacking with weapon",
    "defending with shield",
    "running fast",
    "crouching down",
    "idle breathing animation",
    "taking damage",
    "blocking incoming attack",
    "drinking potion",
    "collecting item",
    "rolling dodge",
    "charging attack",
    "shooting projectile",
    "climbing up",
    "celebrating victory",
    # Complex magical/transformative actions
    "changing dress magically",
    "casting a spell",
    "transforming into different form",
    "teleporting away",
    "summoning creature",
    "creating magical barrier",
    "shapeshifting partially",
    "levitating and floating",
    "creating portal",
    "time manipulation gesture",
    "elemental transformation",
    "merging with shadow",
    "phasing through matter",
    "channeling energy from surroundings",
    "dissolving into particles",
    "materializing from light",
]


def generate_base_sprite(character_prompt: str, index: int) -> Dict:
    """
    FIRST PASS: Generate base pixel art character sprite (square 1:1 ratio)
    """
    # Select a random background color
    bg_color = random.choice(BACKGROUND_COLORS)
    full_prompt = f"{character_prompt}, {PIXEL_ART_BASE} Background color: solid {bg_color}, no transparency, no checkerboard pattern."
    
    print(f"[{index}] 🎨 Generating base sprite: '{character_prompt[:50]}...' (bg: {bg_color})")
    
    try:
        output = replicate.run(
            MODEL,
            input={
                "prompt": full_prompt,
                "resolution": RESOLUTION,
                "image_input": [],
                "aspect_ratio": "1:1",  # Square for character sprites
                "output_format": OUTPUT_FORMAT,
                "safety_filter_level": "block_only_high"
            }
        )
        
        print(f"[{index}] ✅ Base sprite completed!")
        
        return {
            "index": index,
            "character_prompt": character_prompt,
            "background_color": bg_color,
            "url": output,
            "success": True
        }
        
    except Exception as e:
        print(f"[{index}] ❌ Error generating base sprite: {e}")
        return {
            "index": index,
            "character_prompt": character_prompt,
            "success": False,
            "error": str(e)
        }


def generate_action_sprite_sheet(base_image_url: str, character_prompt: str, action: str, index: int, background_color: str = None) -> Dict:
    """
    SECOND PASS: Generate 2x2 sprite sheet with action using base sprite as reference
    """
    # Use the same background color as base sprite, or random if not provided
    bg_color = background_color if background_color else random.choice(BACKGROUND_COLORS)
    full_prompt = f"{character_prompt} performing action: {action}, {SPRITE_SHEET_BASE} Background color: solid {bg_color}, no transparency, no checkerboard pattern."
    
    print(f"[{index}] 🎬 Generating sprite sheet: '{character_prompt[:40]}...' - Action: {action} (bg: {bg_color})")
    
    try:
        output = replicate.run(
            MODEL,
            input={
                "prompt": full_prompt,
                "resolution": RESOLUTION,
                "image_input": [str(base_image_url)],  # Use base sprite as reference
                "aspect_ratio": "1:1",  # Square for 2x2 grid
                "output_format": OUTPUT_FORMAT,
                "safety_filter_level": "block_only_high"
            }
        )
        
        print(f"[{index}] ✅ Sprite sheet completed!")
        
        return {
            "index": index,
            "character_prompt": character_prompt,
            "action": action,
            "background_color": bg_color,
            "url": output,
            "success": True
        }
        
    except Exception as e:
        print(f"[{index}] ❌ Error generating sprite sheet: {e}")
        return {
            "index": index,
            "character_prompt": character_prompt,
            "action": action,
            "success": False,
            "error": str(e)
        }


def download_image(url, filepath: Path) -> bool:
    """Download image from URL and save to local file"""
    try:
        # Convert FileOutput or other objects to string URL
        url_str = str(url)
        urllib.request.urlretrieve(url_str, filepath)
        return True
    except Exception as e:
        print(f"   Download error: {e}")
        return False


def main():
    """
    Main entry point - Two-pass sprite generation:
    1. Generate base pixel art character sprites
    2. Generate action sprite sheets using base sprites as reference
    """
    
    # Create output directories
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("🎮 PIXEL ART SPRITE SHEET GENERATOR")
    print("=" * 70)
    print(f"📝 Characters: {len(CHARACTER_PROMPTS)}")
    print(f"🎬 Available actions: {len(ACTIONS)}")
    print(f"📁 Input folder (base sprites): {INPUT_DIR.absolute()}")
    print(f"📁 Output folder (sprite sheets): {OUTPUT_SPRITES_DIR.absolute()}")
    print(f"🖼️  Resolution: {RESOLUTION}")
    print("=" * 70)
    print()
    
    # ============================================================================
    # FIRST PASS: Generate base pixel art character sprites
    # ============================================================================
    print("🎨 FIRST PASS: Generating base character sprites...")
    print("-" * 70)
    
    base_results = []
    max_workers = min(len(CHARACTER_PROMPTS), 10)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(generate_base_sprite, prompt, i): i 
            for i, prompt in enumerate(CHARACTER_PROMPTS)
        }
        
        for future in as_completed(future_to_index):
            result = future.result()
            base_results.append(result)
    
    base_results.sort(key=lambda x: x["index"])
    
    # Download and save base sprites
    print()
    print("📥 Downloading base sprites to input folder...")
    print("-" * 70)
    
    base_sprites = []  # Store info about successfully saved base sprites
    for result in base_results:
        if result["success"]:
            timestamp = int(time.time() * 1000)
            base_name = f"{timestamp}_{result['index']:03d}_base"
            image_filepath = INPUT_DIR / f"{base_name}.png"
            text_filepath = INPUT_DIR / f"{base_name}.txt"
            
            if download_image(result["url"], image_filepath):
                text_filepath.write_text(result["character_prompt"])
                print(f"[{result['index']}] 💾 Saved: {base_name}.png")
                
                base_sprites.append({
                    "index": result["index"],
                    "character_prompt": result["character_prompt"],
                    "image_path": image_filepath,
                    "base_filename": base_name,  # Store base filename for matching output
                    "url": result["url"],
                    "background_color": result.get("background_color", random.choice(BACKGROUND_COLORS))
                })
            else:
                print(f"[{result['index']}] ❌ Failed to download")
        else:
            print(f"[{result['index']}] ⏭️  Skipped (generation failed)")
    
    print()
    print("=" * 70)
    print(f"✅ First pass complete! {len(base_sprites)}/{len(CHARACTER_PROMPTS)} base sprites saved")
    print("=" * 70)
    print()
    
    if not base_sprites:
        print("❌ No base sprites generated. Exiting.")
        return
    
    # ============================================================================
    # SECOND PASS: Generate action sprite sheets using base sprites as reference
    # ============================================================================
    print("🎬 SECOND PASS: Generating action sprite sheets...")
    print("-" * 70)
    
    sprite_sheet_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_data = {}
        
        for sprite in base_sprites:
            # Pick a random action for this character
            action = random.choice(ACTIONS)
            future = executor.submit(
                generate_action_sprite_sheet,
                sprite["url"],
                sprite["character_prompt"],
                action,
                sprite["index"],
                sprite["background_color"]  # Pass the background color from base sprite
            )
            future_to_data[future] = {
                "sprite": sprite,
                "action": action
            }
        
        for future in as_completed(future_to_data):
            result = future.result()
            # Attach the base filename to the result for later use
            sprite_data = future_to_data[future]
            result["base_filename"] = sprite_data["sprite"]["base_filename"]
            sprite_sheet_results.append(result)
    
    sprite_sheet_results.sort(key=lambda x: x["index"])
    
    # Download and save sprite sheets
    print()
    print("📥 Downloading sprite sheets to output folder...")
    print("-" * 70)
    
    saved_sprite_sheets = 0
    for result in sprite_sheet_results:
        if result["success"]:
            # Use the same filename as the base sprite (matching input/output filenames)
            base_name = result["base_filename"]
            image_filepath = OUTPUT_SPRITES_DIR / f"{base_name}.png"
            text_filepath = OUTPUT_SPRITES_DIR / f"{base_name}.txt"
            
            if download_image(result["url"], image_filepath):
                # Save action description to text file
                prompt_text = f"Character: {result['character_prompt']}\nAction: {result['action']}"
                text_filepath.write_text(prompt_text)
                print(f"[{result['index']}] 💾 Saved: {base_name}.png")
                saved_sprite_sheets += 1
            else:
                print(f"[{result['index']}] ❌ Failed to download")
        else:
            print(f"[{result['index']}] ⏭️  Skipped (generation failed)")
    
    print()
    print("=" * 70)
    print("✨ GENERATION COMPLETE!")
    print("=" * 70)
    print(f"🎨 Base sprites: {len(base_sprites)}/{len(CHARACTER_PROMPTS)} saved to {INPUT_DIR.name}/")
    print(f"🎬 Sprite sheets: {saved_sprite_sheets}/{len(base_sprites)} saved to {OUTPUT_SPRITES_DIR.name}/")
    print(f"📁 Location: {OUTPUT_DIR.absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
