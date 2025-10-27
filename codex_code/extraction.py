import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence


@dataclass
class Entity:
    """Represents a named entity extracted from free-form text."""

    name: str
    type: str
    importance: float


@dataclass
class Relationship:
    """Represents a relationship between two entities."""

    source: str
    target: str
    relation_type: str
    weight: float


class AISuiteLLM:
    """Thin wrapper around aisuite to issue structured prompts."""

    def __init__(self, model: str = "openai:gpt-4o"):
        try:
            from aisuite import Client  # type: ignore
        except ImportError as exc:  # pragma: no cover - aisuite required at runtime
            raise RuntimeError(
                "aisuite is required. Install dependencies with `uv sync`."
            ) from exc

        self._model = model
        self._client = Client()
        self._completions = getattr(self._client.chat, "completions", None)
        if self._completions is None or not hasattr(self._completions, "create"):
            raise RuntimeError(
                "Unsupported aisuite version: chat completions interface not found."
            )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request and return concatenated text output."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self._completions.create(model=self._model, messages=messages)
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "The `openai` package is required. Install dependencies with `uv sync`."
            ) from exc
        except Exception as exc:  # pragma: no cover - surfaced at runtime
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        choices = getattr(response, "choices", None)
        if not choices:
            return str(response)

        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        if message is None:
            return str(response)

        content = getattr(message, "content", None)
        if content is None:
            return str(response)

        if isinstance(content, list):
            chunks: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if text:
                        chunks.append(str(text))
            if chunks:
                return "".join(chunks)
        elif isinstance(content, str):
            return content

        return str(content)


def _parse_json_payload(
    llm: AISuiteLLM,
    system_prompt: str,
    user_prompt: str,
    *,
    max_attempts: int = 2,
) -> Any:
    """Prompt the LLM and parse a JSON payload with a single retry on failure."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        raw_response = llm.complete(system_prompt, user_prompt)
        cleaned = raw_response.strip().strip("`")
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt < max_attempts:
                user_prompt = (
                    f"{user_prompt}\n\n"
                    "Reminder: respond with ONLY valid JSON. No commentary."
                )
    raise ValueError(f"Failed to parse JSON response: {last_error}") from last_error


def _ensure_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def _coerce_entities(raw_entities: Iterable[Dict[str, Any]]) -> List[Entity]:
    entities: List[Entity] = []
    seen = set()
    for item in raw_entities:
        name = str(item.get("name", "")).strip()
        type_ = str(item.get("type", "")).strip()
        if not name:
            continue
        key = (name.lower(), type_.lower())
        if key in seen:
            continue
        seen.add(key)
        importance = _ensure_float(item.get("importance"), default=0.5)
        entities.append(Entity(name=name, type=type_, importance=importance))
    return entities


def _coerce_relationships(
    raw_relationships: Iterable[Dict[str, Any]],
    valid_entities: Sequence[Entity],
) -> List[Relationship]:
    entity_names = {entity.name for entity in valid_entities}
    relationships: List[Relationship] = []
    for item in raw_relationships:
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        relation_type = str(item.get("relation_type", "")).strip()
        if not source or not target or source not in entity_names or target not in entity_names:
            continue
        weight = _ensure_float(item.get("weight"), default=0.5)
        relationships.append(
            Relationship(
                source=source,
                target=target,
                relation_type=relation_type or "related",
                weight=weight,
            )
        )
    return relationships


def extract_entities(text: str, llm: AISuiteLLM) -> List[Entity]:
    """Infer entities from text via the LLM."""
    system_prompt = (
        "You are an information extraction assistant. Extract entities from text. "
        "Return ONLY valid JSON. No prose."
    )
    user_prompt = (
        "Given the following text, list key entities as a JSON array of objects with "
        '`name`, `type`, and `importance` (float 0-1). Use lowercase type labels '
        '(e.g., \"person\", \"organization\"). Importance measures relevance.\n\n'
        f"Text:\n{text}\n\nJSON array:"
    )
    raw_entities = _parse_json_payload(llm, system_prompt, user_prompt)
    if not isinstance(raw_entities, list):
        raise ValueError("Entity extraction returned a non-list payload.")
    return _coerce_entities(raw_entities)


def extract_relationships(
    text: str, entities: Sequence[Entity], llm: AISuiteLLM
) -> List[Relationship]:
    """Infer relationships between entities, given the source text."""
    entity_json = json.dumps([entity.__dict__ for entity in entities], ensure_ascii=False)
    system_prompt = (
        "You are an assistant that maps relationships between known entities. "
        "Only return JSON."
    )
    user_prompt = (
        "Using the provided original text and the list of entities, output an array "
        "of relationship objects. Each object must contain `source`, `target`, "
        "`relation_type`, and `weight` (float 0-1). "
        "Only include relationships explicitly supported by the text.\n\n"
        f"Text:\n{text}\n\nEntities:\n{entity_json}\n\nJSON array:"
    )
    raw_relationships = _parse_json_payload(llm, system_prompt, user_prompt)
    if not isinstance(raw_relationships, list):
        raise ValueError("Relationship extraction returned a non-list payload.")
    return _coerce_relationships(raw_relationships, entities)
