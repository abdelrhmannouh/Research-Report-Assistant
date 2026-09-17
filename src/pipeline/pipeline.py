from groq import BadRequestError
from src.agents.agents import research_agent, llm

MAX_RESEARCH_ATTEMPTS = 3


def _run_research_agent(query: str):
    # gpt-oss-20b occasionally emits malformed JSON for tool call arguments
    # on Groq, which raises a BadRequestError ("tool_use_failed"). Retrying
    # the call resolves it since it's model-generation flakiness, not a
    # real invalid request.
    last_error = None
    for _ in range(MAX_RESEARCH_ATTEMPTS):
        try:
            return research_agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                {"recursion_limit": 10},
            )
        except BadRequestError as e:
            last_error = e
    raise last_error


def pipeline(query: str) -> str:
    # 1. Research (real agent — uses the web_search tool)
    research_response = _run_research_agent(query)
    raw_notes = research_response["messages"][-1].content

    # 2. Analyze (direct LLM call — no tools needed)
    analyst_prompt = (
        "You are a research analyst. You will be given raw, unstructured research "
        "notes on a topic. Your job is to:\n"
        "1. Identify the key facts, insights, and findings from the notes\n"
        "2. Remove irrelevant, repetitive, or low-quality information\n"
        "3. Organize the remaining information into clear, well-structured bullet points, "
        "grouped under short section headings where appropriate\n"
        "4. Do not add new information that wasn't in the original notes\n"
        "5. Do not write a narrative report — only output structured, analyzed bullet points\n\n"
        "Keep your output factual, concise, and easy for someone to turn into a written report.\n\n"
        f"Research notes:\n{raw_notes}"
    )
    analyst_output = llm.invoke(analyst_prompt).content

    # 3. Write (direct LLM call — no tools needed)
    writer_prompt = (
        "You are a professional report writer. You will be given structured, "
        "analyzed bullet points on a topic. Your job is to write a clear, "
        "well-organized report based strictly on that information.\n\n"
        "Your report should include:\n"
        "1. A brief introduction that frames the topic\n"
        "2. A body section that expands on the key points in clear prose "
        "(not just repeating the bullets verbatim)\n"
        "3. A short conclusion that summarizes the main takeaways\n\n"
        "Guidelines:\n"
        "- Do not invent facts or add information not present in the input\n"
        "- Write in a neutral, professional tone\n"
        "- Use clear paragraphs and, where helpful, section headings\n"
        "- Keep the report concise — a few short paragraphs is enough, not an essay\n\n"
        f"Structured points:\n{analyst_output}"
    )
    writer_output = llm.invoke(writer_prompt).content

    return writer_output


if __name__ == "__main__":
    print(pipeline("ai"))