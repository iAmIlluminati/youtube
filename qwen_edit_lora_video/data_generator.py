"""
Pixel Art Character Costume Change Generator using Replicate's google/nano-banana-pro model

Two-pass generation:
1. First pass: Generate base pixel art character sprites (square, 1:1) -> saved to input/
2. Second pass: Generate the same character with different costume using base sprite as reference -> saved to output/
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

# Costume change suffix for second pass (will include background color)
COSTUME_CHANGE_BASE = "Pixel art style, 16-bit retro game sprite, clean pixels, solid colors, no blur, centered character on solid background, front-facing view, same pose and position as reference image but wearing different costume, no transparency."

# Character prompts for base pixel art sprites
CHARACTER_PROMPTS = [
    "Knight in silver armor holding a sword and shield",
    "Wizard in purple robes with pointed hat and staff",
    "Rogue in dark leather armor with dual daggers",
    "Archer in green cloak with bow and quiver",
    "Barbarian warrior with battle axe and fur clothing",
    "Mage in blue robes with glowing orb",
    "Paladin in golden armor with holy symbol",
    "Ninja in black outfit with katana",
    "Pirate with eyepatch, tricorn hat and cutlass",
    "Samurai in traditional armor with katana",
    "Viking with horned helmet and axe",
    "Cyber warrior in futuristic armor with laser gun",
    "Space marine in power armor with rifle",
    "Robot character with mechanical limbs",
    "Elf ranger with longbow and nature-themed clothing",
    "Dwarf warrior with hammer and heavy armor",
    "Alien character with tentacles and advanced technology",
    "Steampunk inventor with goggles and mechanical gadgets",
    "Monk in simple robes with staff",
    "Necromancer in dark robes with skull staff",
    
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

# Pre-mapped costume changes for each character type
# Key: character identifier, Value: list of costume variations
COSTUME_CHANGES = {
    "Knight": [
        "wearing golden ceremonial armor with red cape",
        "wearing dark obsidian armor with purple accents",
        "wearing silver plate armor with blue cape",
        "wearing damaged battle-worn armor with torn cloak",
    ],
    "Wizard": [
        "wearing crimson battle robes with gold trim",
        "wearing white archmage robes with star patterns",
        "wearing dark necromancer robes with skull motifs",
        "wearing emerald green robes with nature symbols",
    ],
    "Rogue": [
        "wearing red assassin outfit with hood",
        "wearing noble's disguise with fancy vest",
        "wearing gray thief outfit with many pockets",
        "wearing black shadow cloak with mask",
    ],
    "Archer": [
        "wearing brown ranger outfit with leaf patterns",
        "wearing royal guard uniform with gold trim",
        "wearing white snow camouflage outfit",
        "wearing dark hunter outfit with fur trim",
    ],
    "Barbarian": [
        "wearing tribal chieftain outfit with feathers",
        "wearing bear pelt armor with bone accessories",
        "wearing war paint and minimal leather armor",
        "wearing horned helmet with wolf pelt cloak",
    ],
    "Mage": [
        "wearing purple arcane robes with mystical runes",
        "wearing white holy vestments with light effects",
        "wearing red fire mage robes with flame patterns",
        "wearing cyan ice mage robes with frost crystals",
    ],
    "Paladin": [
        "wearing white and gold holy armor with wings",
        "wearing silver crusader armor with cross symbol",
        "wearing ornate temple guard armor with gems",
        "wearing battle-worn blessed armor with divine glow",
    ],
    "Ninja": [
        "wearing white shinobi outfit with headband",
        "wearing red assassin garb with mask",
        "wearing purple shadow clan outfit",
        "wearing traditional samurai kimono with katana",
    ],
    "Pirate": [
        "wearing captain's coat with gold buttons",
        "wearing red bandana with leather vest",
        "wearing noble's stolen outfit with jewels",
        "wearing weathered sailor outfit with patches",
    ],
    "Samurai": [
        "wearing ceremonial red and gold armor",
        "wearing black and silver war armor",
        "wearing traditional white and blue kimono",
        "wearing shogun's ornate armor with crest",
    ],
    "Viking": [
        "wearing berserker bear pelt with war paint",
        "wearing chieftain's chainmail with fur cloak",
        "wearing leather armor with Norse symbols",
        "wearing iron plate armor with raven motifs",
    ],
    "Cyber": [
        "wearing stealth black nanosuit with blue lights",
        "wearing heavy combat armor with red accents",
        "wearing white tech suit with holographic display",
        "wearing damaged armor with exposed circuits",
    ],
    "Space": [
        "wearing red commander armor with medals",
        "wearing black ops stealth armor",
        "wearing white explorer suit with scanner",
        "wearing heavy assault armor with weapon mounts",
    ],
    "Robot": [
        "with gold and white plating upgrade",
        "with military green and black armor",
        "with sleek chrome and blue LED lights",
        "with rusty orange and weathered parts",
    ],
    "Elf": [
        "wearing royal elvish robes with gold embroidery",
        "wearing forest scout outfit with leaf patterns",
        "wearing dark elf armor with purple accents",
        "wearing white moonlight robes with silver trim",
    ],
    "Dwarf": [
        "wearing mithril armor with clan symbols",
        "wearing forge master outfit with leather apron",
        "wearing mountain king armor with gems",
        "wearing bronze battle armor with runes",
    ],
    "Alien": [
        "wearing purple energy shield armor",
        "wearing bio-organic exosuit with veins",
        "wearing crystalline armor with glow",
        "wearing tribal alien outfit with tech implants",
    ],
    "Steampunk": [
        "wearing brass and copper inventor outfit",
        "wearing leather aviator gear with goggles",
        "wearing Victorian nobleman attire with gadgets",
        "wearing clockwork armor with gears",
    ],
    "Monk": [
        "wearing orange temple robes with sash",
        "wearing white meditation outfit",
        "wearing red martial arts gi with black belt",
        "wearing traveling monk outfit with straw hat",
    ],
    "Necromancer": [
        "wearing bone armor with skull mask",
        "wearing tattered purple robes with chains",
        "wearing black death knight armor",
        "wearing plague doctor outfit with dark magic",
    ],
    "Druid": [
        "wearing autumn leaf outfit with orange and red",
        "wearing bark armor with living vines",
        "wearing flower crown with spring dress",
        "wearing winter fur with ice crystals",
    ],
    "Bard": [
        "wearing colorful jester outfit with bells",
        "wearing noble's fancy doublet with feathered hat",
        "wearing traveling minstrel outfit with cloak",
        "wearing royal court outfit with golden lute",
    ],
    "Cleric": [
        "wearing golden high priest vestments",
        "wearing battle cleric armor with holy symbols",
        "wearing simple monk robes with prayer beads",
        "wearing white and silver ceremonial outfit",
    ],
    "Assassin": [
        "wearing red and black guild outfit",
        "wearing noble's disguise with hidden weapons",
        "wearing desert assassin robes with scarf",
        "wearing urban stealth suit with mask",
    ],
    "Beastmaster": [
        "wearing druid outfit with animal pelts",
        "wearing tribal hunter gear with totems",
        "wearing ranger outfit with beast claw trophies",
        "wearing shaman robes with feathers and bones",
    ],
    "Alchemist": [
        "wearing purple researcher robes with vials",
        "wearing leather apron with bubbling potions",
        "wearing noble chemist outfit with gold trim",
        "wearing plague doctor outfit with potion belt",
    ],
    "Gunslinger": [
        "wearing black outlaw outfit with poncho",
        "wearing brown sheriff outfit with star badge",
        "wearing red desperado outfit with bandana",
        "wearing fancy gambler outfit with deck of cards",
    ],
    "Shaman": [
        "wearing white spirit guide robes with feathers",
        "wearing tribal chieftain outfit with mask",
        "wearing bone armor with animal skull headdress",
        "wearing nature priest robes with glowing totems",
    ],
    "Demon": [
        "wearing red and black demon slayer armor",
        "wearing holy exorcist robes with crosses",
        "wearing dark hunter outfit with silver weapons",
        "wearing blessed paladin armor with demon trophies",
    ],
    "Time": [
        "wearing Victorian steampunk outfit with gears",
        "wearing futuristic white suit with holographic clock",
        "wearing ancient scholar robes with hourglasses",
        "wearing quantum armor with time distortion effects",
    ],
    "Elemental": [
        "wearing fire-themed red and orange robes with flames",
        "wearing ice-themed blue and white robes with crystals",
        "wearing earth-themed brown and green robes with rocks",
        "wearing storm-themed purple and silver robes with lightning",
    ],
    "Shadow": [
        "wearing dark purple shadow weave outfit",
        "wearing black void armor with red eyes",
        "wearing gray stealth suit with smoke effects",
        "wearing midnight blue rogue outfit with daggers",
    ],
    "Crystal": [
        "wearing prismatic rainbow crystal armor",
        "wearing pink and purple gem-studded robes",
        "wearing transparent quartz armor with light refraction",
        "wearing amethyst mage robes with floating gems",
    ],
    "Mech": [
        "in red and white battle unit with missiles",
        "in blue and silver stealth unit with cloaking",
        "in green and black heavy assault unit",
        "in gold and white commander unit with cape",
    ],
    "Phoenix": [
        "wearing golden flame armor with bright wings",
        "wearing red and orange battle robes with fire aura",
        "wearing white ash and ember outfit",
        "wearing crimson rebirth armor with phoenix feathers",
    ],
}


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


def get_character_type(character_prompt: str) -> str:
    """
    Extract character type from prompt to match with costume changes.
    Returns the matched character type key or None.
    """
    prompt_lower = character_prompt.lower()
    
    for char_type in COSTUME_CHANGES.keys():
        if char_type.lower() in prompt_lower:
            return char_type
    
    # Fallback: return a generic type if no match found
    return None


def generate_costume_change(base_image_url: str, character_prompt: str, costume_description: str, index: int, background_color: str = None) -> Dict:
    """
    SECOND PASS: Generate the same character with different costume using base sprite as reference
    """
    # Use the same background color as base sprite, or random if not provided
    bg_color = background_color if background_color else random.choice(BACKGROUND_COLORS)
    
    # Extract character type from prompt to maintain identity
    character_type = get_character_type(character_prompt)
    
    # Build the costume change prompt
    full_prompt = f"{character_type if character_type else 'Character'} {costume_description}, {COSTUME_CHANGE_BASE} Background color: solid {bg_color}, no transparency, no checkerboard pattern."
    
    print(f"[{index}] 👗 Generating costume change: '{character_prompt[:40]}...' - {costume_description} (bg: {bg_color})")
    
    try:
        output = replicate.run(
            MODEL,
            input={
                "prompt": full_prompt,
                "resolution": RESOLUTION,
                "image_input": [str(base_image_url)],  # Use base sprite as reference
                "aspect_ratio": "1:1",  # Square for character sprite
                "output_format": OUTPUT_FORMAT,
                "safety_filter_level": "block_only_high"
            }
        )
        
        print(f"[{index}] ✅ Costume change completed!")
        
        return {
            "index": index,
            "character_prompt": character_prompt,
            "costume_description": costume_description,
            "background_color": bg_color,
            "url": output,
            "success": True
        }
        
    except Exception as e:
        print(f"[{index}] ❌ Error generating costume change: {e}")
        return {
            "index": index,
            "character_prompt": character_prompt,
            "costume_description": costume_description,
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
    2. Generate costume changes using base sprites as reference
    """
    
    # Create output directories
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("🎮 PIXEL ART CHARACTER COSTUME CHANGE GENERATOR")
    print("=" * 70)
    print(f"📝 Characters: {len(CHARACTER_PROMPTS)}")
    print(f"👗 Character types with costumes: {len(COSTUME_CHANGES)}")
    print(f"📁 Input folder (base sprites): {INPUT_DIR.absolute()}")
    print(f"📁 Output folder (costume changes): {OUTPUT_SPRITES_DIR.absolute()}")
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
    # SECOND PASS: Generate costume changes using base sprites as reference
    # ============================================================================
    print("👗 SECOND PASS: Generating costume changes...")
    print("-" * 70)
    
    costume_change_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_data = {}
        
        for sprite in base_sprites:
            # Get the character type from the prompt
            character_type = get_character_type(sprite["character_prompt"])
            
            # Get appropriate costume change for this character type
            if character_type and character_type in COSTUME_CHANGES:
                costume_description = random.choice(COSTUME_CHANGES[character_type])
            else:
                # Fallback to generic costume if character type not found
                print(f"[{sprite['index']}] ⚠️  Warning: Character type not found for '{sprite['character_prompt'][:50]}...', using generic costume")
                costume_description = "wearing different colored outfit"
            
            future = executor.submit(
                generate_costume_change,
                sprite["url"],
                sprite["character_prompt"],
                costume_description,
                sprite["index"],
                sprite["background_color"]  # Pass the background color from base sprite
            )
            future_to_data[future] = {
                "sprite": sprite,
                "costume_description": costume_description
            }
        
        for future in as_completed(future_to_data):
            result = future.result()
            # Attach the base filename to the result for later use
            sprite_data = future_to_data[future]
            result["base_filename"] = sprite_data["sprite"]["base_filename"]
            costume_change_results.append(result)
    
    costume_change_results.sort(key=lambda x: x["index"])
    
    # Download and save costume changes
    print()
    print("📥 Downloading costume changes to output folder...")
    print("-" * 70)
    
    saved_costume_changes = 0
    for result in costume_change_results:
        if result["success"]:
            # Use the same filename as the base sprite (matching input/output filenames)
            base_name = result["base_filename"]
            image_filepath = OUTPUT_SPRITES_DIR / f"{base_name}.png"
            text_filepath = OUTPUT_SPRITES_DIR / f"{base_name}.txt"
            
            if download_image(result["url"], image_filepath):
                # Save costume description to text file
                prompt_text = f"Character: {result['character_prompt']}\nCostume: {result['costume_description']}"
                text_filepath.write_text(prompt_text)
                print(f"[{result['index']}] 💾 Saved: {base_name}.png")
                saved_costume_changes += 1
            else:
                print(f"[{result['index']}] ❌ Failed to download")
        else:
            print(f"[{result['index']}] ⏭️  Skipped (generation failed)")
    
    print()
    print("=" * 70)
    print("✨ GENERATION COMPLETE!")
    print("=" * 70)
    print(f"🎨 Base sprites: {len(base_sprites)}/{len(CHARACTER_PROMPTS)} saved to {INPUT_DIR.name}/")
    print(f"👗 Costume changes: {saved_costume_changes}/{len(base_sprites)} saved to {OUTPUT_SPRITES_DIR.name}/")
    print(f"📁 Location: {OUTPUT_DIR.absolute()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
