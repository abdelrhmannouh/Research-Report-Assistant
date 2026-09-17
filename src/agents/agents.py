from src.tools.tools import web_search
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent

load_dotenv()

#first researchagent 

llm = ChatGroq(
    # gpt-oss-20b frequently emits malformed JSON for tool call arguments
    # on Groq (groq.BadRequestError: "tool_use_failed"); gpt-oss-120b does
    # not have this problem.
    model = "openai/gpt-oss-120b" ,
    temperature = 0
)
system_prompt = (
    "You are a research assistant. Your job is to research the given topic "
    "using the web_search tool and return clear, organized raw findings/notes. "
    "Do not write a final report — just gather and summarize relevant information."
)

research_agent = create_agent (
    model = llm ,
    system_prompt = system_prompt ,
    tools = [web_search] 

)


