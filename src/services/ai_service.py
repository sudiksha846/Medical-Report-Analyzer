import streamlit as st
from agents.analysis_agent import AnalysisAgent


def init_analysis_state():
    """Initialize analysis-related session state variables."""

    if "analysis_agent" not in st.session_state:
        st.session_state.analysis_agent = AnalysisAgent()

    if "chat_agent" not in st.session_state:
        try:
            from agents.chat_agent import ChatAgent

            if "GROQ_API_KEY" not in st.secrets:
                st.session_state.chat_agent = None
                st.session_state.chat_agent_error = (
                    "GROQ_API_KEY not found in secrets. Please add it."
                )
            else:
                st.session_state.chat_agent = ChatAgent()
                st.session_state.chat_agent_error = None

        except Exception as e:
            st.session_state.chat_agent = None
            st.session_state.chat_agent_error = str(e)



def check_rate_limit():
    init_analysis_state()
    return st.session_state.analysis_agent.check_rate_limit()



def generate_analysis(data, system_prompt):
    """Generate analysis using AnalysisAgent."""
    init_analysis_state()

    return st.session_state.analysis_agent.analyze_report(
        data,
        system_prompt
    )


def get_chat_response(query, context_text, chat_history):
    """Generate chat response using RAG."""

    init_analysis_state()

    if st.session_state.chat_agent is None:
        error_msg = st.session_state.get(
            "chat_agent_error",
            "Chat functionality unavailable. Check GROQ_API_KEY.",
        )
        return f"Error: {error_msg}"

    if not context_text and chat_history:
        for msg in chat_history:
            if msg.get("role") == "system" and "__REPORT_TEXT__" in msg.get("content", ""):
                content = msg.get("content", "")
                start = content.find("__REPORT_TEXT__\n") + len("__REPORT_TEXT__\n")
                end = content.find("\n__END_REPORT_TEXT__")
                if start > 0 and end > start:
                    context_text = content[start:end]
                    break

        if not context_text:
            for msg in reversed(chat_history):
                if msg["role"] == "assistant" and len(msg.get("content", "")) > 100:
                    context_text = msg["content"][:5000]
                    break

    if not context_text:
        context_text = "No report context available."

   
    if (
        "vector_store" not in st.session_state
        or st.session_state.get("vector_store_key") != len(context_text)
    ):
        try:
            with st.spinner("Processing context..."):
                st.session_state.vector_store = (
                    st.session_state.chat_agent.initialize_vector_store(context_text)
                )
                st.session_state.vector_store_key = len(context_text)
        except Exception as e:
            st.warning(f"Vector store failed: {str(e)}")
            return f"Error: Could not process context."

    
    return st.session_state.chat_agent.get_response(
        query,
        st.session_state.vector_store,
        chat_history
    )