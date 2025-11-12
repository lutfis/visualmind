from dotenv import load_dotenv
import aisuite as ai
import json
import networkx as nx
from pyvis.network import Network

load_dotenv()

with open("data/sample_input_ch.txt", "r") as f:
    text = f.read().strip()

client = ai.Client()

# STEP 1: Extract entities
system_prompt = (
    """
    You are an information extraction assistant. Extract entities from text.
    Return ONLY valid JSON. No prose.
    """
)
user_prompt = (
    f"""
    Extract the main entities from the text and return ONLY a JSON array.
    Each entity object must have:
      - "name": string
      - "type": one of ["person","organization","state"] (lowercase only)
      - "importance": float in [0,1]

    Rules:
      - Include only these three types; exclude everything else (events, products, generic locations).
      - "state" = sovereign country or subnational state/province; government bodies/agencies are "organization".
      - No duplicates (deduplicate by canonical name).
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

entities_str = response.choices[0].message.content
entities = json.loads(entities_str)

###########################

system_prompt = (
    """
    You are an information assistant. Determine the synonyms in the given list.
    Return ONLY valid JSON. No prose.
    """
)
user_prompt = (
    f"""
    From json array of entities, determine the entities that are synonyms of each other given the context.
    For examly, "Xi Jinping" and "China" refers to the same thing in the context of the text.
    Merge such entities into one entity object with the JSON structure

    Text:
    {text}

    Input JSON array:
    {entities_str}

    JSON array:
    """
)
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

response = client.chat.completions.create(model="openai:gpt-5-mini-2025-08-07", messages=messages)

print(response.choices[0].message.content)

entities_str = response.choices[0].message.content
entities = json.loads(entities_str)

# STEP 2: Extract relationships
system_prompt = (
    """
    You are an assistant that maps relationships between known entities.
    Return ONLY valid JSON. No prose.
    """
)
user_prompt = (
    f"""
    Using the original text and the extracted entities, return ONLY a JSON array of relationship objects.
    Each relationship object must have:
      - "source": string (exactly matching an entity "name")
      - "target": string (exactly matching an entity "name")
      - "relationship": string
      - "weight": float in [0,1]

    Requirements:
      - Each object must have exactly these keys: "source", "target", "relationship", "weight".
      - "source" and "target" MUST be exact string matches of entity "name" values from the Entities list below. Do not invent, alias, or rename entities. Skip any relation that cannot be mapped to the given names.
      - "relationship" is a short, lowercase label describing the link (e.g., "owner", "director", "founder", "advisor", "loaned money", "negotiated sale", "worked together", "acquired").
      - "weight" is a float in [0,1] reflecting how important this connection is relative to the document's overall context. Consider the explicitness of the statement, centrality to the narrative, strength/frequency of evidence, and the entities' "importance" scores. Use higher weights for explicit, central ties; lower for weak or incidental mentions.
      - Direction: If the text implies direction, set "source" as the actor/subject and "target" as the object/recipient (e.g., "A acquired B" -> source="A", target="B"). If direction is unclear, prefer the conventional direction for the verb; otherwise omit the relation.
      - No duplicates. If the same (source, target, relationship) appears multiple times, include one object with the highest appropriate weight.
      - Only include relationships explicitly supported by the text. If none, return [].
      - Output MUST be valid JSON and nothing else.

    Text:
    {text}

    Entities (use names exactly as provided):
    {entities_str}

    JSON array:
    """
)
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

response = client.chat.completions.create(model="openai:gpt-5-mini-2025-08-07", messages=messages)

print(response.choices[0].message.content)

relationships_str = response.choices[0].message.content
relationships = json.loads(relationships_str)

# STEP 3: Build and render graph
graph = nx.DiGraph()
for entity in entities:
    graph.add_node(
        entity["canonical_name"],
        type=entity["types"],
        value=entity["importance"],
    )
for relation in relationships:
    if relation["source"] not in graph.nodes or relation["target"] not in graph.nodes:
        # Skip relationships referencing unknown entities.
        continue
    graph.add_edge(
        relation["source"],
        relation["target"],
        width=relation["weight"],
        title=relation["relationship"]
    )

nt = Network(directed=True)
nt.from_nx(graph)
nt.write_html('data/output_graph.html')
