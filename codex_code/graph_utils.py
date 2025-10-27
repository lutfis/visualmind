from typing import Iterable

import networkx as nx
from pyvis.network import Network

from codex_code.extraction import Entity, Relationship


def build_graph(
    entities: Iterable[Entity], relationships: Iterable[Relationship]
) -> nx.DiGraph:
    """Create a directed graph with entity importance and relationship weights."""
    graph = nx.DiGraph()
    for entity in entities:
        graph.add_node(
            entity.name,
            **{
                "type": entity.type,
                "importance": entity.importance,
            },
        )
    for relation in relationships:
        if relation.source not in graph.nodes or relation.target not in graph.nodes:
            # Skip relationships referencing unknown entities.
            continue
        graph.add_edge(
            relation.source,
            relation.target,
            relation_type=relation.relation_type,
            weight=relation.weight,
        )
    return graph


def render_graph(
    graph: nx.DiGraph,
    output_path: str,
    *,
    notebook: bool = False,
    height: str = "600px",
    width: str = "100%",
) -> None:
    """Render a graph to PyVis HTML, scaling node size and edge width."""
    visual = Network(height=height, width=width, directed=True, notebook=notebook)
    for node, data in graph.nodes(data=True):
        importance = float(data.get("importance", 0.5))
        size = 10 + importance * 30
        visual.add_node(
            node,
            label=node,
            title=f"{node} ({data.get('type', 'entity')})",
            value=size,
        )
    for source, target, data in graph.edges(data=True):
        weight = float(data.get("weight", 0.5))
        width_ = 1 + weight * 4
        title = f"{data.get('relation_type', 'related')} ({weight:.2f})"
        visual.add_edge(
            source,
            target,
            title=title,
            value=width_,
            width=width_,
        )
    visual.write_html(output_path, open_browser=False)
