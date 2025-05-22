import sys
import requests
import base64
from computer_vision_gpt_approach.computer_vision import  \
    resize_and_encode_image, match_image_to_artwork

# Dictionary mapping long exhibit names to sets of vision tags
ARTWORKS = {
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

def cap_anal():
    response = requests.get("http://127.0.0.1:5000/frame.jpg")
    try:
        if response.status_code == 200:
            encoded_image = base64.b64encode(response.content).decode('utf-8')
            match = match_image_to_artwork(encoded_image, ARTWORKS)
            print(f"[RESULT] Matched artwork: {match}")
            return match

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

# If run directly, execute a test capture
if __name__ == "__main__":
    cap_anal()    
