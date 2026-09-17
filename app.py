import datetime

import streamlit as st

from src.pipeline.pipeline import pipeline

st.set_page_config(
    page_title="Research Report Assistant",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Only style the elements we own (hero banner, report card, footer, chips).
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
        .report-card {
            padding: 1.5rem 1.75rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.10);
            margin-top: 1.25rem;
        }
        .report-card h4 {
            margin-top: 0;
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
        "3. **Write** — produces a polished report"
    )
    st.markdown("---")
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

if "report" not in st.session_state:
    st.session_state.report = None
if "topic" not in st.session_state:
    st.session_state.topic = None
if "error" not in st.session_state:
    st.session_state.error = None

with st.form("research_form"):
    topic = st.text_input(
        "What would you like a report on?",
        placeholder="e.g. The impact of AI on renewable energy",
        label_visibility="visible",
    )
    submitted = st.form_submit_button("Generate Report", use_container_width=True)

if submitted:
    st.session_state.error = None
    if not topic or not topic.strip():
        st.session_state.report = None
        st.warning("Please enter a topic first.")
    else:
        with st.status("Working on your report...", expanded=True) as status:
            try:
                st.write("🔎 Researching the topic on the web...")
                st.write("🧩 Analyzing and structuring the findings...")
                st.write("✍️ Writing the final report...")
                st.session_state.report = pipeline(topic.strip())
                st.session_state.topic = topic.strip()
                status.update(label="Report ready!", state="complete", expanded=False)
            except Exception as e:
                st.session_state.report = None
                st.session_state.error = str(e)
                status.update(label="Something went wrong", state="error", expanded=True)

if st.session_state.error:
    st.error(f"Something went wrong while generating the report: {st.session_state.error}")

if st.session_state.report:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown(f"#### 📄 Report: {st.session_state.topic}")
    st.markdown(st.session_state.report)
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        label="⬇️ Download report as Markdown",
        data=st.session_state.report,
        file_name=f"{st.session_state.topic.lower().replace(' ', '_')}_report.md",
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
