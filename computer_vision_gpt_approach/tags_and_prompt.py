initial_prompt = """
You are a visual tag-based identifier. Below is a list of artworks and objects along with their associated tags.

Your task:
- When I send you an image frame, use only the visual features (tags) from that image to compare against the tags below.
- Return ONLY the name of the artwork or object that best matches the tags from the image.
- You must only return a match if AT LEAST 5 tags from the image are found in that artwork's tag list.
- If no artwork has at least 5 matching tags, reply: "nothing found".

Artwork Tags:

Starry Night:
["starry-night", "van-gogh", "swirling-sky", "yellow-stars", "blue-sky", "cypress-tree", "village-at-night", "expressionist-art", "moon", "blue-and-yellow-painting", "famous-artwork", "post-impressionism", "hillside-village", "painted-nightscape", "dark-cypress", "vibrant-colours", "whirling-clouds", "iconic-night-scene", "yellow-moon", "star-filled-sky"]

Egyptian Style Statue:
["metal-figurine", "brass-statue", "decorative-figure", "ethnic-art", "tribal-sculpture", "african-style-decor", "standing-statue", "woman-holding-bowl", "red-and-black-dress", "golden-bowl", "ornamental-design", "engraved-base", "metallic-doll", "colorful-tribal-figure", "curled-hair-metal", "beaded-neck-ring", "painted-metal-statue", "folk-art-sculpture", "traditional-costume", "bronze-body-figure"]

Toy Dog:
["plush_dog", "brown_dog", "toy_dog", "fabric_dog", "stuffed_animal", "dog_doorstop", "fuzzy_ears", "long_snout", "short_legs", "black_nose", "bead_eyes", "stitched_mouth", "bow_collar", "leather_texture", "soft_toy", "dog_figurine", "cute_dog", "floppy_ears", "round_body", "miniature_dog"]

Sunflowers (Van Gogh):
["sunflowers", "vase with flowers", "cut flowers", "drooping sunflowers", "tightly packed bouquet", "green stems", "brown flower centers", "yellow petals", "wilted petals", "green sepals", "asymmetric flower positions", "monochromatic yellow scheme", "warm ochre background", "earthy tones", "muted greens", "light cream vase", "blue outline around vase", "subtle orange highlights", "low contrast shadows", "post-impressionist style", "Van Gogh signature on vase", "textured impasto brushwork", "visible directional strokes", "thick paint application", "organic irregular shapes"]

Liberty Leading the People:
["romanticism", "oil painting", "large canvas", "historical painting", "Eugène Delacroix", "revolutionary scene", "French flag", "red white blue", "Liberty figure", "bare-breasted woman", "battlefield", "smoke and chaos", "dramatic lighting", "dynamic composition", "foreground bodies", "tricolour flag", "weaponry", "dark background", "heroic symbolism", "crowded scene"]

Mona Lisa:
["portrait", "woman", "smile", "Leonardo da Vinci", "Renaissance", "oil painting", "dark clothing", "natural background", "realism", "subtle lighting", "sfumato", "soft shading", "classical art", "famous painting", "mystery", "brown tones", "long hair", "folded hands", "calm expression", "detailed brushwork"]

The Scream:
["the scream", "edvard munch", "screaming figure", "hands on face", "open mouth", "oval head", "bulging eyes", "flowing robe", "twisting body", "wavy lines", "swirling sky", "orange sky", "vivid colours", "expressionist style", "emotional intensity", "distorted proportions", "bold brushstrokes", "contrasting tones", "isolated figure", "psychological expression"]

From now on, you will be given a single image at a time.
Use ONLY visual tags from the image to find the closest matching artwork from the list above.

IMPORTANT: Only return a result if at least 5 tags from the image are found in one of the artworks' tag sets. If not, reply:
"nothing found".
"""

starry_night_tags = [
    "starry-night",
    "van-gogh",
    "swirling-sky",
    "yellow-stars",
    "blue-sky",
    "cypress-tree",
    "village-at-night",
    "expressionist-art",
    "moon",
    "blue-and-yellow-painting",
    "famous-artwork",
    "post-impressionism",
    "hillside-village",
    "painted-nightscape",
    "dark-cypress",
    "vibrant-colours",
    "whirling-clouds",
    "iconic-night-scene",
    "yellow-moon",
    "star-filled-sky"
]

egyptian_style_statue = [
    "metal-figurine",
    "brass-statue",
    "decorative-figure",
    "ethnic-art",
    "tribal-sculpture",
    "african-style-decor",
    "standing-statue",
    "woman-holding-bowl",
    "red-and-black-dress",
    "golden-bowl",
    "ornamental-design",
    "engraved-base",
    "metallic-doll",
    "colorful-tribal-figure",
    "curled-hair-metal",
    "beaded-neck-ring",
    "painted-metal-statue",
    "folk-art-sculpture",
    "traditional-costume",
    "bronze-body-figure"
]

dog_tags = [
    "plush_dog",
    "brown_dog",
    "toy_dog",
    "fabric_dog",
    "stuffed_animal",
    "dog_doorstop",
    "fuzzy_ears",
    "long_snout",
    "short_legs",
    "black_nose",
    "bead_eyes",
    "stitched_mouth",
    "bow_collar",
    "leather_texture",
    "soft_toy",
    "dog_figurine",
    "cute_dog",
    "floppy_ears",
    "round_body",
    "miniature_dog"
]

sunflowers_vangogh_tags = [
    "sunflowers",
    "vase with flowers",
    "cut flowers",
    "drooping sunflowers",
    "tightly packed bouquet",
    "green stems",
    "brown flower centers",
    "yellow petals",
    "wilted petals",
    "green sepals",
    "asymmetric flower positions",
    "monochromatic yellow scheme",
    "warm ochre background",
    "earthy tones",
    "muted greens",
    "light cream vase",
    "blue outline around vase",
    "subtle orange highlights",
    "low contrast shadows",
    "post-impressionist style",
    "Van Gogh signature on vase",
    "textured impasto brushwork",
    "visible directional strokes",
    "thick paint application",
    "organic irregular shapes"
]

liberty_leading_people_tags = [
    "romanticism",
    "oil painting",
    "large canvas",
    "historical painting",
    "Eugène Delacroix",
    "revolutionary scene",
    "French flag",
    "red white blue",
    "Liberty figure",
    "bare-breasted woman",
    "battlefield",
    "smoke and chaos",
    "dramatic lighting",
    "dynamic composition",
    "foreground bodies",
    "tricolour flag",
    "weaponry",
    "dark background",
    "heroic symbolism",
    "crowded scene"
]

mona_lisa_tags = [
    "portrait",
    "woman",
    "smile",
    "Leonardo da Vinci",
    "Renaissance",
    "oil painting",
    "dark clothing",
    "natural background",
    "realism",
    "subtle lighting",
    "sfumato",
    "soft shading",
    "classical art",
    "famous painting",
    "mystery",
    "brown tones",
    "long hair",
    "folded hands",
    "calm expression",
    "detailed brushwork"
]

scream_tags = [
    "the scream",
    "edvard munch",
    "screaming figure",
    "hands on face",
    "open mouth",
    "oval head",
    "bulging eyes",
    "flowing robe",
    "twisting body",
    "wavy lines",
    "swirling sky",
    "orange sky",
    "vivid colours",
    "expressionist style",
    "emotional intensity",
    "distorted proportions",
    "bold brushstrokes",
    "contrasting tones",
    "isolated figure",
    "psychological expression"
]








