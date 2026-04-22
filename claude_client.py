import anthropic
from config import CLAUDE_API_KEY, CLAUDE_MODEL, SYSTEM_PROMPT

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


async def generate_response(user_message: str, history: list[dict] | None = None) -> str:
    """调用 Claude API 生成回复"""
    messages = []
    if history:
        for msg in history:
            messages.append(
                {"role": msg["role"], "content": msg["content"]}
            )
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=CLAUDE_MODEL,
        system=SYSTEM_PROMPT,
        messages=messages,
        max_tokens=4096,
    )

    return response.content[0].text
