"""Streamlit chat interface for the clinical text to SQL agent."""

import os

import pandas as pd
import streamlit as st

from agent import DB_PATH, run_agent

st.set_page_config(page_title="Clinical Text to SQL Agent", page_icon=":bar_chart:", layout="wide")
st.title("Clinical Text to SQL Agent")
st.caption("Ask questions in plain English. The agent writes, runs, and explains the SQL. Synthetic data only.")

if not os.path.exists(DB_PATH):
    st.warning("Database not found. Run `python setup_db.py` first.")
    st.stop()

with st.sidebar:
    st.header("Example questions")
    examples = [
        "How many patients are in each department?",
        "Which 5 patients had the most visits?",
        "What is the average glucose value by sex?",
        "How many lab results were outside the reference range?",
        "List patients diagnosed with hypertension in 2025",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex

question = st.chat_input("Ask a question about the clinical database")
if "pending" in st.session_state:
    question = st.session_state.pop("pending")

if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Writing and running SQL..."):
            result = run_agent(question, verbose=False)
        st.markdown(result["summary"])
        if result["rows"]:
            st.dataframe(pd.DataFrame(result["rows"], columns=result["columns"]))
        with st.expander("Generated SQL"):
            st.code(result["sql"], language="sql")
