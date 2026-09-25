from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

SYSTEM_PROMPT = (
    "You are a research assistant. Your job is to research the given topic "
    "using the web_search tool and return clear, organized raw findings/notes. "
    "Search results are numbered like [1], [2]; after each fact in your notes, "
    "cite the number(s) of the result(s) it came from. "
    "Do not write a final report — just gather and summarize relevant information."
)


def build_research_agent(llm: BaseChatModel, web_search: BaseTool):
    return create_agent(model=llm, system_prompt=SYSTEM_PROMPT, tools=[web_search])
