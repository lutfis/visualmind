Project Requirement Document

Title: Simple Text-to-Graph Script Using aisuite

⸻

1. Objective

Create a Python script that:
	1.	Takes a raw text input (e.g. a news article).
	2.	Calls a Large Language Model (LLM) through the aisuite package.
	3.	Performs three sequential steps using multiple LLM calls:
	•	Extract entities (nodes).
	•	Identify relationships (edges).
	•	Generate a graph visualization.
	4.	Produces a final HTML or image file showing the network of entities and their relationships.

This is a simplified version of the multi-agent project, focusing only on aisuite and sequential logic (no CrewAI or AutoGen).

⸻

2. Functional Requirements

Step 1: Entity Extraction
	•	Use the LLM to identify key entities (people, organizations, countries, products, etc.) from the given text.
	•	For each entity, generate:
	•	name (string)
	•	type (string, e.g., “person”, “organization”)
	•	importance (float between 0–1)
	•	Output format: JSON list.

Example Output

[
  {"name": "Google", "type": "organization", "importance": 0.9},
  {"name": "DeepMind", "type": "organization", "importance": 0.8}
]


⸻

Step 2: Relationship Extraction
	•	Pass both the original text and entities list to the LLM.
	•	Ask the LLM to identify relationships between these entities.
	•	For each relationship, include:
	•	source (entity name)
	•	target (entity name)
	•	relation_type (string)
	•	weight (float 0–1, strength of relationship)

Example Output

[
  {"source": "Google", "target": "DeepMind", "relation_type": "acquired", "weight": 0.95}
]


⸻

Step 3: Graph Construction and Visualization
	•	Use Python libraries:
	•	networkx for graph structure.
	•	pyvis for interactive visualization (HTML output).
	•	The node size should scale with importance, and edge width with weight.
	•	Save final visualization as output_graph.html.

⸻

3. Technical Requirements

Component	Requirement
Language	Python 3.13
Libraries	aisuite, networkx, pyvis, pydantic (optional for schema validation)
Input Format	Plain text string
Output Format	Interactive HTML graph (e.g., output_graph.html)
LLM Provider	Use OpenAI via AISuite (openai:gpt-4o or openai:gpt-4-turbo)
API Keys	Read from .env file (AISUITE_API_KEY, OPENAI_API_KEY)
Error Handling	Handle invalid JSON responses gracefully; retry once if parsing fails.
Logging	Print progress logs for each step.


⸻

4. File Structure

project/
│
├── main.py                # Orchestrates steps 1-3
├── extraction.py          # Functions for entity/relation extraction (LLM calls)
├── graph_utils.py         # Graph construction and visualization logic
├── .env                   # Contains API keys
├── requirements.txt       # Required packages
└── sample_input.txt       # Example input text


⸻

5. Example Workflow

Input (sample_input.txt):

In 2014, Google acquired DeepMind, a British AI company, to advance its artificial intelligence research.

Expected console output:

[1] Extracting entities...
[2] Extracting relationships...
[3] Building and rendering graph...
Graph saved to output_graph.html

Expected graph (output_graph.html):
	•	Nodes: “Google”, “DeepMind”
	•	Edge: “acquired” (Google → DeepMind)
	•	Node sizes reflect importance; edge width reflects weight.

⸻

6. Evaluation Criteria
	•	✅ Correct sequence of steps using multiple LLM calls via AISuite.
	•	✅ Clear logging and error handling.
	•	✅ Produces a coherent, viewable graph.
	•	✅ Readable and modular code.
	•	✅ No dependencies on LangChain, CrewAI, or AutoGen.
	•	✅ Documented in README.md with setup instructions.
