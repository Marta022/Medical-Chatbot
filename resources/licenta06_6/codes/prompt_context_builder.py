def get_base_system_prompt() -> str:
    """Return the loaded base system prompt."""

    return BASE_SYSTEM_PROMPT


def build_context_block(context_lines: list[str]) -> str:
    """Build the retrieval context block injected into generation prompts."""

    return (
        CONTEXT_BLOCK_HEADER
        + "\n"
        + "\n".join(f"{CONTEXT_BULLET_PREFIX}{line}" for line in context_lines)
    )
