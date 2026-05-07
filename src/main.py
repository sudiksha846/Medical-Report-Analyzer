
import streamlit as st
from auth.session_manager import SessionManager
from components.auth_pages import show_login_page
from components.sidebar import show_sidebar
from components.analysis_form import show_analysis_form
from components.footer import show_footer
from config.app_config import APP_NAME, APP_TAGLINE, APP_DESCRIPTION, APP_ICON
from services.ai_service import get_chat_response
st.set_page_config(
    page_title="DocuDoc | AI Medical Analyzer", layout="wide", initial_sidebar_state= "collapsed"
)

SessionManager.init_session()

st.markdown(
    """
    <style>
        .stApp {
            background-color: #301934;     
        }
        /* Hide form submission helper text */
        div[data-testid="InputInstructions"] > span:nth-child(1) {
            visibility: hidden;
        }
    </style>
""",
    unsafe_allow_html=True,
)

def show_welcome_screen():
    st.markdown(
        f"""
        <div style='text-align: center; padding: 50px;'>
            <h1>{APP_ICON} {APP_NAME}</h1>
            <h3>{APP_DESCRIPTION}</h3>
            <p style='font-size: 1.2em; color: #666;'>{APP_TAGLINE}</p>
            <p>Start by creating a new analysis session</p>
        </div>
        """,
        unsafe_allow_html=True,
    )



    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        if st.button(
            "➕ New Analysis Session", use_container_width=True, type="primary"
        ):
            success, session = SessionManager.create_chat_session()
            if success:
                st.session_state.current_session = session
                st.rerun()
            else:
                st.error("Failed to create session")


def show_chat_history():
    success, messages = st.session_state.auth_service.get_session_messages(
        st.session_state.current_session["id"]
    )

    if success:
        for msg in messages:
            
            if msg.get("role") == "system":
                continue
            if msg["role"] == "user":
                st.info(msg["content"])
            else:
                st.success(msg["content"])
        return messages
    return []


def handle_chat_input(messages):
    if prompt := st.chat_input("Ask a follow-up question about the report..."):
        # Display user message immediately
        st.info(prompt)

    
        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session["id"], prompt, role="user"
        )

       
        context_text = st.session_state.get("current_report_text", "")

        if not context_text and messages:
            for msg in messages:
                if msg.get("role") == "system" and "__REPORT_TEXT__" in msg.get(
                    "content", ""
                ):
                    content = msg.get("content", "")
                    start_idx = content.find("__REPORT_TEXT__\n") + len(
                        "__REPORT_TEXT__\n"
                    )
                    end_idx = content.find("\n__END_REPORT_TEXT__")
                    if start_idx > len("__REPORT_TEXT__\n") - 1 and end_idx > start_idx:
                        context_text = content[start_idx:end_idx]
                       
                        st.session_state.current_report_text = context_text
                        break

        with st.spinner("Thinking..."):
            response = get_chat_response(prompt, context_text, messages)

            st.success(response)

            
            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"], response, role="assistant"
            )
           
            st.rerun()


def show_user_greeting():
    if st.session_state.user:
        
        display_name = st.session_state.user.get("name") or st.session_state.user.get(
            "email", ""
        )
        st.markdown(
            f"""
            <div style='text-align: right; padding: 1.4rem; color: #42A5F5; font-size: 1.2em;'>
                 Hello, {display_name}
            </div>
        """,
            unsafe_allow_html=True,
        )


def main():
    SessionManager.init_session()

    if not SessionManager.is_authenticated():
        show_login_page()
        show_footer()
        return

    show_user_greeting()

  
    show_sidebar()

   
    if st.session_state.get("current_session"):
        st.title(f" {st.session_state.current_session['title']}")
        messages = show_chat_history()

       
        if messages:
        
            with st.expander("New Analysis / Update Report", expanded=False):
                show_analysis_form()

            handle_chat_input(messages)
        else:
            show_analysis_form()
    else:
        show_welcome_screen()


if __name__ == "__main__":
    main()
