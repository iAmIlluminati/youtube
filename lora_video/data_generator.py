"""
Data Generator using Replicate's google/nano-banana-pro model
Generates images from prompts in parallel with random aspect ratios
"""

import os
import random
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import replicate


# Configuration
MODEL = "google/nano-banana-pro"
OUTPUT_DIR = Path(__file__).parent / "generated_images"
ASPECT_RATIOS = ["16:9", "1:1", "4:3", "3:4"]
RESOLUTION = "1K"
OUTPUT_FORMAT = "png"

# Common suffix appended to all prompts when calling the API
PROMPT_SUFFIX = "\n\nARTSTYLE : Rick and Morty Show art style. Follow the prompt exactly and ensure the art style is accurate to the show, dont add anything extra which is not mentioned in prompt."  # e.g. ", high quality, detailed, 4k"

# Sample prompts - modify as needed
PROMPTS = [
    # PORTRAITS - Famous personalities
    "Close-up portrait of Albert Einstein with wild white hair and mustache, wearing brown tweed jacket, thoughtful expression, chalkboard with E=mc² equation in background, warm study lighting",
    "Portrait of Steve Jobs in his iconic black turtleneck and round glasses, confident expression, standing in minimalist modern office with sleek technology visible in background, soft dramatic lighting",
    "Side profile portrait of Mahatma Gandhi with round glasses, bald head, wrapped in white cloth, peaceful serene smile, simple background with spinning wheel visible, natural daylight",
    "Portrait of Marie Curie in early 1900s dark dress, hair pulled back, determined expression, laboratory setting with glass bottles and scientific equipment, warm ambient lighting",
    
    # OUTDOOR SCENES - Various times of day
    "Wide shot of a futuristic alien marketplace at high noon, purple sky with two suns, bizarre alien vendors with tentacles selling glowing fruits, crystalline buildings in background, crowds of diverse alien species",
    "Suburban neighborhood street at golden hour sunset, tree-lined sidewalk with fallen autumn leaves, kids riding bicycles, houses with warm lights turning on, orange and pink sky",
    "Dense jungle scene at dawn with heavy morning mist, ancient stone temple ruins covered in vines, shafts of blue-tinted early morning light breaking through the canopy, exotic birds flying",
    "Snowy mountain peak at dusk, lone adventurer in heavy winter coat standing at edge looking at vast purple-blue twilight sky, stars beginning to appear, distant valley below",
    "Desert landscape at midday with intense sun, bizarre rock formations creating dramatic shadows, small figure in spacesuit examining strange geometric crystals protruding from sand",
    
    # INDOOR SCENES - Different settings
    "Cluttered basement laboratory at night, workbench covered with electronic parts and wiring, multiple monitors showing complex equations, sparking Tesla coil in corner, blue glow illuminating the scene",
    "Cozy coffee shop interior in early morning, barista preparing drinks, steam rising from espresso machine, warm yellow lighting, customers sitting at wooden tables, rain visible through large windows",
    "High-tech spaceship cockpit at night, pilot seat facing massive windshield showing star field and distant nebula, holographic control panels glowing blue and orange, dashboard lights",
    "School cafeteria at lunch time, long tables filled with students eating, lunch lady serving food, fluorescent lighting, motivational posters on walls, chaos and conversation",
    "Dark medieval castle throne room lit by torches, ornate stone throne with purple cushions, tall stained glass windows, suits of armor lining the walls, mysterious shadows",
    
    # ACTION SCENES - Dynamic moments
    "Mid-action shot of person in lab coat running through portal, half their body in normal living room and half entering swirling green interdimensional gateway, furniture being pulled toward portal",
    "Dramatic scene of figure with jetpack flying over neon-lit cyberpunk city at night, trailing smoke, towering skyscrapers with holographic advertisements, flying cars in background",
    "Underwater scene at depth, diver in yellow submarine suit face to face with massive bioluminescent sea creature with dozens of eyes, deep blue water, shafts of light from surface above",
    "Chase scene in busy alien bazaar, character pushing through crowd of bizarre aliens, market stalls with strange goods toppling over, dust and debris, afternoon lighting with colored awnings",
    
    # ENVIRONMENTAL SCENES - Establishing shots
    "Post-apocalyptic cityscape at dusk, overgrown skyscrapers with vegetation, broken windows, abandoned cars covered in vines, orange sunset breaking through clouds, birds circling",
    "Mystical forest clearing at midnight, giant ancient tree in center with door in trunk, mushrooms glowing blue around base, fireflies, full moon visible through branches, ethereal mist",
    "Retro-futuristic 1950s-style diner on asteroid, visible space and Earth through large panoramic windows, chrome interior, neon signs, aliens and humans sitting at counter, afternoon",
    "Vast ice cave interior, massive blue ice formations creating natural pillars and arches, frozen waterfall, explorer with flashlight creating beam of light through ice crystals, cold blue ambient light",
    
    # CHARACTER INTERACTIONS - Multiple subjects
    "Two scientists arguing in laboratory, one pointing at whiteboard covered in complex equations while other holds tablet showing holographic projection, evening light through window, tense body language",
    "Family dinner scene around table at evening, four people passing dishes, warm overhead lighting, kitchen visible in background, realistic suburban dining room, casual modern clothing",
    "Robot and human shaking hands in sleek white office, large window showing futuristic city skyline at sunset, professional setting, chrome and glass furniture",
    
    # UNUSUAL PERSPECTIVES
    "Bird's eye view of person lying in grass field at noon, arms spread out, surrounded by wildflowers, their shadow clearly visible, bright summer day",
    "Extreme low angle looking up at person standing at edge of tall building, geometric architecture, dramatic clouds in sky, sunset lighting creating silhouette",
    "First-person perspective view of hands holding glowing artifact in dark ancient temple, mysterious symbols on walls illuminated by artifact's blue light, nighttime exploration",
    "Fish-eye lens view of crowded space station observation deck, curved glass dome showing cosmos above, dozens of beings looking up at stars and planets, circular room, futuristic seating",
    
    # ICONIC PLACES IRL - Famous real-world landmarks
    "The Statue of Liberty on Liberty Island at midday, bright sunlight, clear blue sky, tourists on ferry in foreground, New York City skyline visible in distance across the water",
    "Times Square in New York City at night, massive LED billboards and neon signs illuminating the scene, crowds of people walking, yellow taxis, steam rising from manholes, vibrant colors",
    "Grand Canyon vista point at sunrise, dramatic red and orange rock formations, layers of canyon walls visible, small figures standing at edge viewing platform, purple morning sky",
    "Great Wall of China snaking across mountain ridges, ancient stone fortifications, watchtowers visible along the wall, green mountains, clear afternoon sky, distant misty peaks",
    "Egyptian pyramids of Giza at sunset, massive stone structures, Sphinx in middle ground, tourists on camels, golden desert sand, dramatic orange sky with sun on horizon",
    "Mount Everest peak from base camp perspective, snow-covered summit piercing clouds, prayer flags in foreground, tents and climbers preparing, harsh bright sunlight on ice and snow",
    
]


def generate_image(prompt: str, index: int) -> dict:
    """Generate a single image from a prompt using Replicate API"""
    aspect_ratio = random.choice(ASPECT_RATIOS)
    full_prompt = prompt + PROMPT_SUFFIX  # Append common suffix for API call
    
    print(f"[{index}] 🚀 Starting: '{prompt[:50]}...' (aspect: {aspect_ratio})")
    
    try:
        # replicate.run() handles polling internally and returns the final output
        output = replicate.run(
            MODEL,
            input={
                "prompt": full_prompt,
                "resolution": RESOLUTION,
                "image_input": [],
                "aspect_ratio": aspect_ratio,
                "output_format": OUTPUT_FORMAT,
                "safety_filter_level": "block_only_high"
            }
        )
        
        print(f"[{index}] ✅ Completed!")
        
        return {
            "index": index,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "url": output,
            "success": True
        }
        
    except Exception as e:
        print(f"[{index}] ❌ Error: {e}")
        return {
            "index": index,
            "prompt": prompt,
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
    """Main entry point - generates images in parallel and saves them"""
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("🍌 Nano Banana Pro Image Generator")
    print("=" * 60)
    print(f"📝 Prompts: {len(PROMPTS)}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")
    print(f"📐 Aspect ratios: {ASPECT_RATIOS}")
    print(f"🖼️  Resolution: {RESOLUTION}")
    print("=" * 60)
    print()
    
    # Run all generations in parallel using ThreadPoolExecutor
    results = []
    max_workers = min(len(PROMPTS), 10)  # Limit concurrent requests
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(generate_image, prompt, i): i 
            for i, prompt in enumerate(PROMPTS)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            result = future.result()
            results.append(result)
    
    # Sort results by index for consistent ordering
    results.sort(key=lambda x: x["index"])
    
    print()
    print("=" * 60)
    print("📥 Downloading images...")
    print("=" * 60)
    
    # Download all successful images
    saved_count = 0
    for result in results:
        if result["success"]:
            timestamp = int(time.time() * 1000)
            aspect_safe = result["aspect_ratio"].replace(":", "x")
            base_name = f"{timestamp}_{result['index']:03d}_{aspect_safe}"
            image_filepath = OUTPUT_DIR / f"{base_name}.png"
            text_filepath = OUTPUT_DIR / f"{base_name}.txt"
            
            if download_image(result["url"], image_filepath):
                # Save prompt to text file with same name
                text_filepath.write_text(result["prompt"])
                print(f"[{result['index']}] 💾 Saved: {base_name}.png + .txt")
                saved_count += 1
            else:
                print(f"[{result['index']}] ❌ Failed to download")
        else:
            print(f"[{result['index']}] ⏭️  Skipped (generation failed)")
    
    print()
    print("=" * 60)
    print(f"✨ Done! Generated {saved_count}/{len(PROMPTS)} images")
    print(f"📁 Location: {OUTPUT_DIR.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
