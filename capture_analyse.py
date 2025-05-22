import sys
import requests
import base64
from computer_vision_gpt_approach.computer_vision import  \
    resize_and_encode_image, match_image_to_artwork

ARTWORKS = {
    "Starry Night": {
        "starry-night", "van-gogh", "swirling-sky", "yellow-stars", "blue-sky",
        "cypress-tree", "village-at-night", "expressionist-art", "moon",
        "blue-and-yellow-painting", "famous-artwork", "post-impressionism"
    },
    "Stylized Egyptian Sculpture": {
        "metal-figurine", "brass-statue", "decorative-figure", "ethnic-art",
        "tribal-sculpture", "african-style-decor", "woman-holding-bowl",
        "red-and-black-dress", "ornamental-design", "engraved-base",
        "painted-metal-statue", "folk-art-sculpture", "bronze-body-figure"
    },
    "Toy Dog": {
        "plush_dog", "brown_dog", "toy_dog", "fabric_dog", "stuffed_animal",
        "dog_doorstop", "bead_eyes", "bow_collar", "floppy_ears", "round_body"
    },
    "Sunflowers (Van Gogh)": {
        "sunflowers", "vase with flowers", "yellow petals", "wilted petals",
        "green stems", "warm ochre background", "post-impressionist style",
        "Van Gogh signature", "textured impasto brushwork"
    },
    "Liberty Leading the People": {
        "romanticism", "oil painting", "historical painting", "Eugène Delacroix",
        "revolutionary scene", "French flag", "bare-breasted woman", "tricolour flag",
        "heroic symbolism"
    },
    "Mona Lisa": {
        "portrait", "woman", "smile", "Leonardo da Vinci", "Renaissance",
        "sfumato", "folded hands", "calm expression"
    },
    "The Scream": {
        "the scream", "edvard munch", "screaming figure", "hands on face",
        "swirling sky", "expressionist style", "vivid colours", "psychological expression"
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

cap_anal()
