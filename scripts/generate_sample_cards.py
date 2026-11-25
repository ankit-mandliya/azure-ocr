import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Directory for sample cards
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def create_english_sample_card(output_path: Path) -> None:
    """Create a sample English/Latin visiting card image."""
    width, height = 700, 400
    image = Image.new("RGB", (width, height), color=(248, 249, 250))
    draw = ImageDraw.Draw(image)

    # Accent decorative bar
    draw.rectangle([(0, 0), (25, height)], fill=(37, 99, 235))
    draw.rectangle([(25, 0), (35, height)], fill=(96, 165, 250))

    try:
        font_large = ImageFont.truetype("arial.ttf", 32)
        font_medium = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_large = font_medium = font_small = ImageFont.load_default()

    # Person Name & Job Title
    draw.text((60, 50), "Rajesh Sharma", fill=(17, 24, 39), font=font_large)
    draw.text((60, 95), "Chief Technology Officer", fill=(75, 85, 99), font=font_medium)

    # Divider line
    draw.line([(60, 135), (640, 135)], fill=(229, 231, 235), width=2)

    # Company Details
    draw.text((60, 160), "Apex Software Technologies Pvt Ltd", fill=(31, 41, 55), font=font_medium)
    draw.text((60, 195), "124 Park Avenue, Sector 5, Cyber City", fill=(107, 114, 128), font=font_small)
    draw.text((60, 220), "Bangalore, Karnataka - 560001", fill=(107, 114, 128), font=font_small)

    # Contact Details
    draw.text((60, 275), "Phone: +91 98765 43210", fill=(31, 41, 55), font=font_small)
    draw.text((60, 305), "Email: rajesh.sharma@apextechnologies.com", fill=(37, 99, 235), font=font_small)
    draw.text((60, 335), "Web: https://www.apextechnologies.com", fill=(37, 99, 235), font=font_small)

    image.save(output_path, quality=95)
    print(f"Created sample English card: {output_path}")


def create_hindi_sample_card(output_path: Path) -> None:
    """Create a sample Devanagari/Hindi visiting card image."""
    width, height = 700, 400
    image = Image.new("RGB", (width, height), color=(255, 253, 245))
    draw = ImageDraw.Draw(image)

    # Decorative header
    draw.rectangle([(0, 0), (width, 15)], fill=(217, 119, 6))

    # Fallback to system fonts that support Devanagari if available
    devanagari_fonts = ["mangal.ttf", "nirmala.ttf", "arial.ttf"]
    font_large = font_medium = font_small = ImageFont.load_default()

    for font_name in devanagari_fonts:
        try:
            font_large = ImageFont.truetype(font_name, 32)
            font_medium = ImageFont.truetype(font_name, 20)
            font_small = ImageFont.truetype(font_name, 16)
            break
        except IOError:
            continue

    # Name and Title
    draw.text((50, 45), "विकास शर्मा", fill=(17, 24, 39), font=font_large)
    draw.text((50, 90), "प्रबंध निदेशक (Managing Director)", fill=(120, 53, 15), font=font_medium)

    # Divider
    draw.line([(50, 130), (650, 130)], fill=(251, 191, 36), width=2)

    # Company
    draw.text((50, 155), "नमस्ते सॉल्यूशंस प्राइवेट लिमिटेड", fill=(31, 41, 55), font=font_medium)
    draw.text((50, 190), "Namaste Solutions Pvt Ltd", fill=(75, 85, 99), font=font_small)
    draw.text((50, 220), "एम.जी. रोड, प्लॉट नंबर 45, इंदौर (म.प्र.)", fill=(107, 114, 128), font=font_small)

    # Contact details
    draw.text((50, 270), "संपर्क: +91 91234 56789", fill=(31, 41, 55), font=font_small)
    draw.text((50, 300), "ईमेल: contact@namastesolutions.in", fill=(180, 83, 9), font=font_small)
    draw.text((50, 330), "वेबसाइट: https://www.namastesolutions.in", fill=(180, 83, 9), font=font_small)

    image.save(output_path, quality=95)
    print(f"Created sample Hindi card: {output_path}")


def main():
    english_card = SAMPLES_DIR / "sample_english_card.jpg"
    hindi_card = SAMPLES_DIR / "sample_hindi_card.jpg"

    create_english_sample_card(english_card)
    create_hindi_sample_card(hindi_card)
    print(f"\nAll sample cards generated in: {SAMPLES_DIR}")


if __name__ == "__main__":
    main()

