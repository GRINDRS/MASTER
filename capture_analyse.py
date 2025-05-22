import sys
import cv2
from computer_vision_gpt_approach.computer_vision import  \
    resize_and_encode_image, match_image_to_artwork

# Updated ARTWORKS dict (using long exhibit names) for compatibility with voicebot.py and computer_vision.py
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

def cap_anal() -> str:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot access webcam")
        sys.exit(1)

    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to capture frame")
        sys.exit(1)

    filename = "frame.jpg"
    cv2.imwrite(filename, frame)
    print("[INFO] Frame captured. Analyzing...")
    
    try:
        encoded = resize_and_encode_image(filename)
        match = match_image_to_artwork(encoded, ARTWORKS)
        print(f"[RESULT] Matched artwork: {match}")
        cap.release()
        cv2.destroyAllWindows()
        
        return match

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

cap_anal()    
