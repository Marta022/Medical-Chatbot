def _llamaindex_semantic_chunks(text: str) -> list[str]:
    """Split text with the strict LlamaIndex semantic splitter."""

    try:
        from llama_index.core.node_parser import SemanticSplitterNodeParser
        from llama_index.core.schema import Document
    except Exception:
        return []

    try:
        parser = SemanticSplitterNodeParser.from_defaults(
            buffer_size=SEMANTIC_SPLITTER_BUFFER_SIZE,
            breakpoint_percentile_threshold=SEMANTIC_BREAKPOINT_PERCENTILE,
        )
        nodes = parser.get_nodes_from_documents([Document(text=text)])
    except Exception:
        return []

    chunks = [re.sub(r"\s+", " ", node.get_content()).strip() for node in nodes]
    return [chunk for chunk in chunks if chunk]


def semantic_chunks(
    text: str,
    *,
    max_chars: int = DEFAULT_SEMANTIC_MAX_CHARS,
    use_llamaindex: bool = True,
) -> list[str]:
    """Run strict semantic chunking after structure-aware preparation."""

    cleaned = text.strip()
    if not cleaned:
        return []
    blocks = _group_lines_with_markdown_structure(cleaned)
    if not blocks:
        return []
    prepared_text = "\n\n".join(blocks)

    if not use_llamaindex:
        raise RuntimeError("Semantic chunking requires llama-index semantic splitter.")
    semantic = _llamaindex_semantic_chunks(prepared_text)
    if not semantic:
        raise RuntimeError("Semantic chunking requires a working llama-index semantic splitter.")
    return semantic


def chunk_text(
    text: str,
    strategy: str = DEFAULT_STRATEGY,
    *,
    semantic_max_chars: int = DEFAULT_SEMANTIC_MAX_CHARS,
    semantic_use_llamaindex: bool = True,
) -> list[str]:
    """Dispatch one of the supported raw-text chunking strategies."""

    normalized = (strategy or DEFAULT_STRATEGY).strip().lower()
    if normalized == "section":
        return section_chunks(text)
    if normalized == "semantic":
        return semantic_chunks(
            text,
            max_chars=semantic_max_chars,
            use_llamaindex=semantic_use_llamaindex,
        )
    raise ValueError(f"Unknown chunking strategy: {strategy}")
