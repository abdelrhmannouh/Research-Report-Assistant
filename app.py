import datetime

import streamlit as st

from src.client import ReportClient, ReportError
from src.config import get_settings
from src.models import ReportResult

client = ReportClient(get_settings().api_url)

st.set_page_config(
    page_title="Research Report Assistant",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Only style the elements we own (hero banner, footer, form).
# Core widgets are left to the theme in .streamlit/config.toml so they stay
# legible and consistent across Streamlit versions.
st.markdown(
    """
    <style>
        .hero {
            padding: 1.75rem 2rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            color: #ffffff;
            font-size: 1.9rem;
            font-weight: 700;
            margin: 0 0 0.35rem 0;
        }
        .hero p {
            color: rgba(255, 255, 255, 0.92);
            font-size: 1rem;
            margin: 0;
        }
        .footer {
            text-align: center;
            color: rgba(245, 245, 247, 0.45);
            font-size: 0.82rem;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        div[data-testid="stForm"] {
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 14px;
            padding: 1.25rem 1.25rem 0.5rem 1.25rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🧭 About")
    st.write(
        "This assistant researches a topic on the web, distills the findings, "
        "and writes a clean, structured report — all in one pipeline."
    )
    st.markdown("### ⚙️ How it works")
    st.markdown(
        "1. **Research** — searches the web via Tavily\n"
        "2. **Analyze** — extracts and organizes key facts\n"
        "3. **Write** — produces a polished report with cited sources"
    )
    st.markdown("---")
    st.caption(f"Backend: {client.mode}")
    st.caption(f"© {datetime.date.today().year} Abdelrhman Nouh. All rights reserved.")

st.markdown(
    """
    <div class="hero">
        <h1>Research Report Assistant</h1>
        <p>Turn any topic into a well-researched, well-written report in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

STAGES = {
    "research": ("🔎", "Researching the topic on the web", "Research"),
    "analyze": ("🧩", "Analyzing and structuring the findings", "Analysis"),
    "write": ("✍️", "Writing the final report", "Writing"),
}

st.session_state.setdefault("result", None)
st.session_state.setdefault("error", None)

with st.form("research_form"):
    topic = st.text_input(
        "What would you like a report on?",
        placeholder="e.g. The impact of AI on renewable energy",
        max_chars=300,
    )
    submitted = st.form_submit_button("Generate Report", use_container_width=True)

if submitted:
    st.session_state.error = None
    topic = (topic or "").strip()
    if len(topic) < 3:
        st.warning("Please enter a topic (at least 3 characters).")
    else:
        st.session_state.result = None
        with st.status("Working on your report...", expanded=True) as status:
            lines = {stage: st.empty() for stage in STAGES}
            try:
                for item in client.stream(topic):
                    if isinstance(item, ReportResult):
                        st.session_state.result = item
                        continue
                    icon, doing, done = STAGES[item.stage]
                    if item.status == "started":
                        status.update(label=f"{doing}...")
                        lines[item.stage].markdown(f"{icon} {doing}...")
                    else:
                        extra = f", {item.detail}" if item.detail else ""
                        lines[item.stage].markdown(
                            f"✅ {done} done in {item.elapsed:.1f}s{extra}"
                        )
                total = sum(st.session_state.result.timings.values())
                status.update(
                    label=f"Report ready in {total:.0f}s", state="complete", expanded=False
                )
            except ReportError as e:
                st.session_state.error = str(e)
                status.update(label="Something went wrong", state="error", expanded=True)

if st.session_state.error:
    st.error(st.session_state.error)

result = st.session_state.result
if result:
    with st.container(border=True):
        st.markdown(f"#### 📄 Report: {result.topic}")
        st.markdown(result.report)
        if result.sources:
            st.markdown("##### Sources")
            st.markdown(
                "\n".join(f"{s.id}. [{s.title}]({s.url})" for s in result.sources)
            )

    st.download_button(
        label="⬇️ Download report as Markdown",
        data=result.to_markdown(),
        file_name=result.filename,
        mime="text/markdown",
        use_container_width=True,
    )

st.markdown(
    f"""
    <div class="footer">
        © {datetime.date.today().year} Abdelrhman Nouh — Research Report Assistant. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True,
)
