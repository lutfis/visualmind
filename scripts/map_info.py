from dotenv import load_dotenv
import aisuite as ai
import json
import networkx as nx
from pyvis.network import Network
from openai import OpenAI
import base64

load_dotenv()

with open("data/map_input.txt", "r") as f:
    text = f.read().strip()

client = ai.Client()

system_prompt = (
    """
    You are an information extraction assistant. Extract locations from text.
    Return ONLY valid JSON. No prose.
    """
)
user_prompt = (
    f"""
    Read the text carefully and identify distinct locations. Return ONLY a JSON array representing a table of rows.
    Each row/object must include:
      - "name": canonical name (string)
      - "place_type": one of ["country","state","province","county","city"] (lowercase only)
    And other fields as they are present in the text.

    Rules:
      - Include only locations ("country","state","province","county","city").
      - Exclude people, organizations, events, products, and dates.
      - Deduplicate by canonical location; merge aliases and counts.
      - If none found, return [].

    Text:
    {text}

    JSON array:
    """
)
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

response = client.chat.completions.create(model="openai:gpt-5-mini-2025-08-07", messages=messages)

print(response.choices[0].message.content)

locations_str = response.choices[0].message.content
locations = json.loads(locations_str)


system_prompt = (
    """
    You are an mapping and infographics assistant. Create a map visualization based on location data.
    Return ONLY valid visualization data. No prose.
    """
)
user_prompt = (
    f"""
    Read the text, which is in JSON format representing a table of locations.
    Show the locations on a map that includes all of the locations but not other surrounding geography as much as possible.
    Then annotate each location with its name and the other fields present in the data.

    Text:
    {locations_str}

    JSON array:
    """
)
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

# Call OpenAI's Image API directly (no AI Suite) to generate a map image
openai_client = OpenAI()

# Flatten the chat-style prompt into a single prompt string for image generation
_prompt_text = system_prompt + "\n" + user_prompt

image_response = openai_client.images.generate(
    model="gpt-image-1",
    prompt=_prompt_text,
    size="1024x1024",
)

# Save the first returned image to disk (with basic safety checks)
_data = getattr(image_response, "data", None) or []
if not _data:
    raise RuntimeError("OpenAI Images API returned no data")

_first = _data[0]
_b64 = getattr(_first, "b64_json", None)
if not _b64:
    raise RuntimeError("OpenAI Images API did not include b64_json on the first result")

_img_bytes = base64.b64decode(_b64)
output_path = "data/map.png"
with open(output_path, "wb") as _f:
    _f.write(_img_bytes)

print(f"Map image generated and saved to: {output_path}")