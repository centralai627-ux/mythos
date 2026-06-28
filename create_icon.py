"""
Mythos Icon Generator
====================
Generates ICO file from SVG for Windows shortcuts.
"""
from __future__ import annotations
import os
from pathlib import Path

def create_ico() -> bool:
    """Create ICO file from PNG using Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "pillow", "-q"])
        from PIL import Image, ImageDraw
    
    # ICO output path
    ico_path = Path(__file__).parent / "Mythos Desktop APp" / "desktop" / "assets" / "mythos.ico"
    ico_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create icon at multiple sizes
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        img = create_mythos_icon(size)
        images.append(img)
    
    # Save as ICO
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    
    print(f"Icon created: {ico_path}")
    return True


def create_mythos_icon(size: int) -> Image.Image:
    """Create a Mythos icon at the specified size."""
    from PIL import Image, ImageDraw
    
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate proportions
    center = size // 2
    scale = size / 256  # Scale relative to 256px base
    
    # Colors
    cyan = (100, 220, 255, 255)
    purple = (168, 85, 247, 255)
    dark = (10, 10, 20, 255)
    white = (255, 255, 255, 200)
    
    # Draw background circle
    bg_radius = int(120 * scale)
    draw.ellipse(
        [center - bg_radius, center - bg_radius, center + bg_radius, center + bg_radius],
        fill=dark,
        outline=cyan,
        width=max(1, int(2 * scale))
    )
    
    # Draw crystal wings (simplified diamond shape)
    wing_points = [
        (center, int(80 * scale)),   # Top
        (int(180 * scale), center),   # Right
        (center, int(176 * scale)),   # Bottom
        (int(76 * scale), center),    # Left
    ]
    
    # Outer diamond
    draw.polygon(wing_points, outline=cyan, fill=None)
    
    # Inner diamond with gradient effect
    inner_points = [
        (center, int(100 * scale)),
        (int(160 * scale), center),
        (center, int(156 * scale)),
        (int(96 * scale), center),
    ]
    draw.polygon(inner_points, fill=(*cyan[:3], 100))
    
    # Center core
    core_radius = int(20 * scale)
    draw.ellipse(
        [center - core_radius, center - core_radius, center + core_radius, center + core_radius],
        fill=cyan
    )
    
    # Inner bright core
    inner_radius = int(10 * scale)
    draw.ellipse(
        [center - inner_radius, center - inner_radius, center + inner_radius, center + inner_radius],
        fill=white
    )
    
    # Draw "M" letter
    if size >= 32:
        font_size = int(24 * scale)
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), "M", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = center - text_width // 2
        text_y = center - text_height // 2 + int(2 * scale)
        
        draw.text((text_x, text_y), "M", fill=dark, font=font)
    
    return img


def create_png() -> bool:
    """Create PNG versions of the icon."""
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed.")
        return False
    
    assets_dir = Path(__file__).parent / "Mythos Desktop APp" / "desktop" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PNG at different sizes
    sizes = {
        "icon-16.png": 16,
        "icon-32.png": 32,
        "icon-48.png": 48,
        "icon-64.png": 64,
        "icon-128.png": 128,
        "icon-256.png": 256,
        "icon.png": 256,  # Default
    }
    
    for filename, size in sizes.items():
        img = create_mythos_icon(size)
        img.save(assets_dir / filename)
        print(f"Created: {filename}")
    
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  MYTHOS AI - Icon Generator")
    print("=" * 50)
    
    print("\nGenerating PNG icons...")
    create_png()
    
    print("\nGenerating ICO file...")
    create_ico()
    
    print("\nDone!")
