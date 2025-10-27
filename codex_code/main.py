import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from codex_code.extraction import AISuiteLLM, extract_entities, extract_relationships
from codex_code.graph_utils import build_graph, render_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an entity relationship graph from raw text."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("sample_input.txt"),
        help="Path to the input text file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output_graph.html"),
        help="Output path for the HTML visualization.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai:gpt-4o",
        help="aisuite model identifier (e.g., openai:gpt-4o).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    text = args.input.read_text(encoding="utf-8").strip()
    if not text:
        print("Input text is empty.", file=sys.stderr)
        sys.exit(1)

    llm = AISuiteLLM(model=args.model)

    print("[1] Extracting entities...")
    entities = extract_entities(text, llm)

    print("[2] Extracting relationships...")
    relationships = extract_relationships(text, entities, llm)

    print("[3] Building and rendering graph...")
    graph = build_graph(entities, relationships)
    render_graph(graph, str(args.output))
    print(f"Graph saved to {args.output}")


if __name__ == "__main__":
    main()
