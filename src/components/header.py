import streamlit as st

def show_header():
    if st.session_state.user:
        display_name = st.session_state.user.get('name') or st.session_state.user.get('email', '')
        st.markdown(f"""
            <div style='text-align: right; padding: 1.2rem; color: #1565C0; font-size: 1.0em;'>
                Hello, {display_name}
            </div>
        """, unsafe_allow_html=True)
