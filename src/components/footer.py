import streamlit as st
from config.app_config import PRIMARY_COLOR, SECONDARY_COLOR

def show_footer(in_sidebar=False):
    base_styles = f"""
        text-align: center;
        padding: 0.8rem;
        background: linear-gradient(to right, 
            rgba(156, 39, 176, 0.04),
            rgba(206, 147, 216, 0.06),
            rgba(156, 39, 176, 0.04)
        );
        border-top: 1px solid rgba(76, 175, 80, 0.15);
        margin-top: {'0' if in_sidebar else '2rem'};
        {'width: 100%' if not in_sidebar else ''};
        box-shadow: 0 -2px 10px rgba(233, 30, 99, 0.05);
    """
    
    st.markdown(
        f"""
        <div style='{base_styles}'>
            <div style='
                font-family: "Source Sans Pro", sans-serif;
                color: #64B5F6;
                font-size: 0.75rem;
                letter-spacing: 0.02em;
                margin: 0;
                opacity: 0.95;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 8px;
            '>
             © 2026 DocuDoc • AI Medical Report Analyzer
            </div>
        </div>
    
        """,
        unsafe_allow_html=True
    )
