from dotenv import load_dotenv
import aisuite as ai
import json
import networkx as nx
from pyvis.network import Network

load_dotenv()

with open("data/sample_input.txt", "r") as f:
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
    Given the following text, list key entities as a JSON array of objects with
    `name`, `type`, and `importance` (float 0-1). Use lowercase type labels
    (e.g., \"person\", \"organization\"). Importance measures relevance.
    Text:\n{text}\n\nJSON array:
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
    Using the provided original text and the list of entities, output an array 
    of relationship objects. Each object must contain `source`, `target`, 
    `relation_type`, and `weight` (float 0-1). 
    Only include relationships explicitly supported by the text.\n\n
    Text:\n{text}\n\nEntities:\n{entities_str}\n\nJSON array:
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
        entity["name"],
        type=entity["type"],
        value=entity["importance"],
    )
for relation in relationships:
    if relation["source"] not in graph.nodes or relation["target"] not in graph.nodes:
        # Skip relationships referencing unknown entities.
        continue
    graph.add_edge(
        relation["source"],
        relation["target"],
        weight=relation["weight"],
        relation_type=relation["relation_type"]
    )

nt = Network(directed=True)
nt.from_nx(graph)
nt.write_html('data/output_graph.html')