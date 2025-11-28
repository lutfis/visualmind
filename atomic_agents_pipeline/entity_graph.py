from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Literal

import instructor
import networkx as nx
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import Field
from pyvis.network import Network

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator


EntityType = Literal["person", "organization", "state"]


class DescribedIOSchema(BaseIOSchema):
    """Base schema that keeps docstrings intact for dynamically generated subclasses."""

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        if not (cls.__doc__ and cls.__doc__.strip()):
            for base in cls.__mro__[1:]:
                doc = getattr(base, "__doc__", "")
                if doc and doc.strip():
                    cls.__doc__ = doc
                    break
        super().__pydantic_init_subclass__(**kwargs)


class EntityExtractionInput(DescribedIOSchema):
    """Input payload that carries the document text that needs entity extraction."""

    text: str = Field(..., description="Full document text to analyze for entities.")


class EntityCandidate(DescribedIOSchema):
    """Single entity mention candidate extracted from the document."""

    name: str = Field(..., description="Entity surface form exactly as referenced.")
    entity_type: EntityType = Field(..., description="One of person, organization, or state (lowercase).")
    importance: float = Field(..., ge=0.0, le=1.0, description="Relative prominence in [0,1].")


class EntityExtractionOutput(DescribedIOSchema):
    """Collection of entity candidates detected in the document."""

    entities: List[EntityCandidate] = Field(default_factory=list, description="Candidate entity list.")


class SynonymResolutionInput(DescribedIOSchema):
    """Inputs required to group synonymous entities back to a canonical record."""

    text: str = Field(..., description="Original article text.")
    candidates: List[EntityCandidate] = Field(..., description="Entity candidates produced in the previous step.")


class CanonicalEntity(DescribedIOSchema):
    """Canonical entity definition after synonym merging."""

    canonical_name: str = Field(..., description="Primary name for the deduplicated entity.")
    types: List[EntityType] = Field(..., min_length=1, description="One or more entity types for this record.")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance weight inherited from the text context.")
    members: List[str] = Field(default_factory=list, description="Names or aliases merged into this canonical entity.")


class SynonymResolutionOutput(DescribedIOSchema):
    """Normalized entity list after synonym merging."""

    entities: List[CanonicalEntity] = Field(default_factory=list, description="Canonical entity records.")


class RelationshipExtractionInput(DescribedIOSchema):
    """Inputs necessary to map relationships between canonical entities."""

    text: str = Field(..., description="Original article text.")
    entities: List[CanonicalEntity] = Field(..., description="Canonical entities that relationships must reference.")


class RelationshipRecord(DescribedIOSchema):
    """Directed relationship record between two canonical entities."""

    source: str = Field(..., description="Canonical entity acting as the source/subject.")
    target: str = Field(..., description="Canonical entity acting as the target/object.")
    relationship: str = Field(..., description="Lowercase label describing the relationship.")
    weight: float = Field(..., ge=0.0, le=1.0, description="Importance weight in [0,1].")


class RelationshipExtractionOutput(DescribedIOSchema):
    """Relationship set generated from the text."""

    relationships: List[RelationshipRecord] = Field(default_factory=list, description="Directed relationships.")


def _build_entity_agent(client: instructor.client.Instructor) -> AtomicAgent[EntityExtractionInput, EntityExtractionOutput]:
    prompt = SystemPromptGenerator(
        background=[
            "You are an information extraction assistant focused on geopolitical text.",
            "Your only job is to list the main people, organizations, or states referenced in the provided document.",
        ],
        steps=[
            "Review the supplied text carefully.",
            "Identify distinct entities that strongly influence the narrative.",
            "Assign an importance score between 0 and 1 where higher means the document focuses on that entity.",
        ],
        output_instructions=[
            "Never invent entities not mentioned in the text.",
            "Only use the entity types person, organization, or state (all lowercase).",
            "Return the entities in the order they matter to the document.",
        ],
    )
    return AtomicAgent[EntityExtractionInput, EntityExtractionOutput](
        config=AgentConfig(
            client=client,
            model="gpt-5-mini",
            system_prompt_generator=prompt,
        ) # type: ignore
    )


def _build_synonym_agent(
    client: instructor.client.Instructor,
) -> AtomicAgent[SynonymResolutionInput, SynonymResolutionOutput]:
    prompt = SystemPromptGenerator(
        background=[
            "You collapse duplicate entities so that graph analytics work on canonical nodes.",
            "Two entries describe the same canonical entity if one is a synonym, alias, or obvious reference for the other in context.",
        ],
        steps=[
            "Study the article text and the candidate list.",
            "Cluster names that refer to the same underlying real-world actor.",
            "It is important to merge the nodes that mean the same thing in the context, for example Vladimir Putin and Russia or Xi Jinping and China mean the same thing in geopolitical context."
            "Select a single canonical_name for each cluster and carry over representative metadata.",
        ],
        output_instructions=[
            "Keep canonical_name strings consistent and human-readable.",
            "List every alias you merged into members.",
            "Use the allowed entity types only; multiple types should stay unique and in lowercase.",
            "Importance must stay in [0,1]; inherit the max or average importance from the merged members.",
        ],
    )
    return AtomicAgent[SynonymResolutionInput, SynonymResolutionOutput](
        config=AgentConfig(
            client=client,
            model="gpt-5-mini",
            system_prompt_generator=prompt,
        )
    )


def _build_relationship_agent(
    client: instructor.client.Instructor,
) -> AtomicAgent[RelationshipExtractionInput, RelationshipExtractionOutput]:
    prompt = SystemPromptGenerator(
        background=[
            "You map directed relationships between previously defined canonical entities.",
            "Only include relationships that the text states or clearly implies.",
        ],
        steps=[
            "Review the text to understand how the canonical entities interact.",
            "Map each interaction into a single directed edge with a short lowercase label.",
            "Scale the weight to [0,1] based on how central the relationship is to the document.",
        ],
        output_instructions=[
            "Do not invent entities; source/target must exactly match canonical_name values.",
            "Skip edges that do not have both endpoints in the canonical list.",
            "Use the strongest reading of directionality (actor -> recipient).",
        ],
    )
    return AtomicAgent[RelationshipExtractionInput, RelationshipExtractionOutput](
        config=AgentConfig(
            client=client,
            model="gpt-5-mini",
            system_prompt_generator=prompt,
        )
    )


def _build_client() -> instructor.client.Instructor:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set before running the atomic-agents pipeline.")
    return instructor.from_openai(OpenAI(api_key=api_key))


def _render_graph(entities: List[CanonicalEntity], relationships: List[RelationshipRecord], output_html: Path) -> None:
    graph = nx.DiGraph()
    for entity in entities:
        graph.add_node(
            entity.canonical_name,
            type=", ".join(entity.types),
            value=entity.importance,
            members=", ".join(entity.members),
        )

    known_nodes = set(graph.nodes)
    for relation in relationships:
        if relation.source not in known_nodes or relation.target not in known_nodes:
            continue
        graph.add_edge(
            relation.source,
            relation.target,
            width=relation.weight,
            title=relation.relationship,
        )

    network = Network(directed=True)
    network.from_nx(graph)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    network.write_html(str(output_html))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a relationship graph using Atomic Agents.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/sample_input_ch.txt"),
        help="Path to the input text file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output_graph.html"),
        help="Path to the HTML file that will store the PyVis graph.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = _parse_args()
    text = args.input.read_text(encoding="utf-8").strip()

    client = _build_client()
    entity_agent = _build_entity_agent(client)
    synonym_agent = _build_synonym_agent(client)
    relationship_agent = _build_relationship_agent(client)

    entity_result = entity_agent.run(EntityExtractionInput(text=text))
    canonical_result = synonym_agent.run(
        SynonymResolutionInput(
            text=text,
            candidates=entity_result.entities,
        )
    )
    relationship_result = relationship_agent.run(
        RelationshipExtractionInput(
            text=text,
            entities=canonical_result.entities,
        )
    )

    print("Entities:", entity_result.model_dump_json(indent=2))
    print("Canonical Entities:", canonical_result.model_dump_json(indent=2))
    print("Relationships:", relationship_result.model_dump_json(indent=2))

    _render_graph(canonical_result.entities, relationship_result.relationships, args.output)
    print(f"Graph written to {args.output}")


if __name__ == "__main__":
    main()
