import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agent.config import settings


def get_llm() -> ChatGroq:
    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    return ChatGroq(
        model=settings.groq_model,
        temperature=0.2,
        groq_api_key=settings.groq_api_key,
    )


def invoke_json(system: str, user: str) -> dict:
    llm = get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
    )
    content = response.content if isinstance(response.content, str) else str(response.content)
    content = re.sub(r"^```json\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)
    return json.loads(content)