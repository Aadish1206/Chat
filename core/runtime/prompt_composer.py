from __future__ import annotations


def compose_final_prompt(
    base_system_prompt: str,
    usecase_format_prompt: str,
    tool_outputs: list[dict],
    citations: list[str],
    user_message: str,
) -> str:
    rendered_outputs = "\n\n".join([str(x) for x in tool_outputs])
    citation_block = "\n".join(f"- {c}" for c in citations)
    return (
        f"{base_system_prompt}\n\n"
        f"{usecase_format_prompt}\n\n"
        "## Tool Outputs\n"
        f"{rendered_outputs}\n\n"
        "## Citations\n"
        f"{citation_block}\n\n"
        "## User Question\n"
        f"{user_message}"
    )
