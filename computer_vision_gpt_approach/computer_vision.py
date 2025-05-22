import openai
import base64
import os
import sys
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import cv2
from typing import Any

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def resize_and_encode_image(image_path: str, max_size:int =512):
    print(f"[INFO] Loading image from: {image_path}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    try:
        img = Image.open(image_path)
        img.thumbnail((max_size, max_size))
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        print(f"[INFO] Image successfully encoded. Length: {len(encoded)} characters")
        return encoded
    except Exception as e:
        print(f"[ERROR] Failed to process image: {e}")
        sys.exit(1)

def match_image_to_artwork(encoded_image: Any, artworks: Any):
    try:

        artwork_lines = "\n".join([
            f"{name}: {', '.join(tags)}"
            for name, tags in artworks.items()
        ])

        system_prompt = f"""You are a smart visual analyst.

You will be shown an image. First, describe it in detail, noting visual features, artistic style, material, and purpose.

Then, compare it to this list of artworks and determine the best match, based on concept, style, and visual similarity.

Only return the name of the matched artwork, or "nothing found" if there's no good match.

Artworks:
{artwork_lines}
"""

        print("[INFO] Sending image and matching request to OpenAI...")
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]}
            ],
            max_tokens=200,
        ) # type: ignore

        result: str = response.choices[0].message.content.strip()  # type: ignore
        return result
    except Exception as e:
        print(f"[ERROR] OpenAI API failed: {e}")
        return "nothing found"

if __name__ == "__main__":
    artworks = {
        "The Scream by Edvard Munch": {
            "the scream", "edvard munch", "screaming figure", "hands on face",
            "swirling sky", "expressionist style", "vivid colours", "psychological expression"
        },
        "Starry Night by Vincent van Gogh": {
            "starry-night", "van-gogh", "swirling-sky", "yellow-stars", "blue-sky",
            "cypress-tree", "village-at-night", "expressionist-art", "moon",
            "blue-and-yellow-painting", "famous-artwork", "post-impressionism"
        },
        "Sunflowers by Vincent van Gogh": {
            "sunflowers", "vase with flowers", "yellow petals", "wilted petals",
            "green stems", "warm ochre background", "post-impressionist style",
            "Van Gogh signature", "textured impasto brushwork"
        },
        "Liberty Leading the People by Eugène Delacroix": {
            "romanticism", "oil painting", "historical painting", "Eugène Delacroix",
            "revolutionary scene", "French flag", "bare-breasted woman", "tricolour flag",
            "heroic symbolism"
        },
        "Mona Lisa by Leonardo da Vinci": {
            "portrait", "woman", "smile", "Leonardo da Vinci", "Renaissance",
            "sfumato", "folded hands", "calm expression"
        },
        "Ancient Egyptian Statue": {
            "metal-figurine", "brass-statue", "decorative-figure", "ethnic-art",
            "tribal-sculpture", "african-style-decor", "woman-holding-bowl",
            "red-and-black-dress", "ornamental-design", "engraved-base",
            "painted-metal-statue", "folk-art-sculpture", "bronze-body-figure"
        },
        "Plushy Dog Sculpture": {
            "plush_dog", "brown_dog", "toy_dog", "fabric_dog", "stuffed_animal",
            "dog_doorstop", "bead_eyes", "bow_collar", "floppy_ears", "round_body"
        }
    }

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot access webcam")
        sys.exit(1)

    print("Press ENTER to capture a frame for analysis. Press ESC to exit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to capture frame")
            break

        cv2.imshow("Press ENTER to analyze frame", frame)
        key = cv2.waitKey(1)

        if key == 13:  
            filename = "frame.jpg"
            cv2.imwrite(filename, frame)
            print("[INFO] Frame captured. Analyzing...")
            try:
                encoded = resize_and_encode_image(filename)
                match = match_image_to_artwork(encoded, artworks)
                print(f"[RESULT] Matched artwork: {match}")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif key == 27:  
            print("[INFO] Exiting.")
            break

    cap.release()
    cv2.destroyAllWindows()
