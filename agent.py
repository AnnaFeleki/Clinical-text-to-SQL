"""Text to SQL agent with a self correction loop and a read only guard."""

import re
import sqlite3
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

DB_PATH = "clinical.db"
CHAT_MODEL = "gpt-4o-mini"
MAX_RETRIES = 3
ROW_LIMIT = 50

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|pragma|vacuum)\b",
    re.IGNORECASE,
)


def get_schema(db_path: str = DB_PATH) -> str:
    """Return the CREATE TABLE statements for every table."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    conn.close()
    return "\n\n".join(row[0] for row in rows)


def is_safe(sql: str) -> bool:
    """Allow only a single SELECT statement."""
    stripped = sql.strip().rstrip(";")
    if ";" in stripped:
        return False
    if not stripped.lower().startswith(("select", "with")):
        return False
    return not FORBIDDEN.search(stripped)


def extract_sql(text: str) -> str:
    """Pull SQL out of a fenced code block if present."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip()


def execute(sql: str, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchmany(ROW_LIMIT)
        return columns, rows
    finally:
        conn.close()


def run_agent(question: str, db_path: str = DB_PATH, verbose: bool = True) -> dict:
    """Answer a natural language question. Returns dict with sql, rows, columns, summary."""
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    schema = get_schema(db_path)

    messages = [
        SystemMessage(
            content=(
                "You are an expert SQLite analyst. Write ONE read only SQL query "
                "that answers the user's question.\n"
                f"Schema:\n{schema}\n\n"
                "Rules: SQLite dialect. SELECT statements only. "
                f"Always include LIMIT {ROW_LIMIT} unless aggregating to few rows. "
                "Return ONLY the SQL inside a ```sql code block, nothing else."
            )
        ),
        HumanMessage(content=question),
    ]

    sql, columns, rows = "", [], []
    for attempt in range(1, MAX_RETRIES + 1):
        response = llm.invoke(messages)
        sql = extract_sql(response.content)

        if not is_safe(sql):
            error = "Query rejected: only single SELECT statements are allowed."
        else:
            try:
                columns, rows = execute(sql, db_path)
                break
            except sqlite3.Error as exc:
                error = f"SQLite error: {exc}"

        if verbose:
            print(f"Attempt {attempt} failed: {error}")
        messages.append(response)
        messages.append(HumanMessage(content=f"{error}\nPlease fix the query."))
    else:
        return {"sql": sql, "columns": [], "rows": [], "summary": "Could not produce a valid query."}

    preview = [dict(zip(columns, row)) for row in rows[:20]]
    summary_prompt = [
        SystemMessage(
            content="Summarize the SQL result for a non technical user in 2 or 3 sentences. "
                    "Mention concrete numbers. Do not mention SQL."
        ),
        HumanMessage(content=f"Question: {question}\nResult rows: {preview}"),
    ]
    summary = llm.invoke(summary_prompt).content

    return {"sql": sql, "columns": columns, "rows": rows, "summary": summary}


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How many patients are in each department?"
    result = run_agent(question)
    print(f"\nSQL:\n{result['sql']}\n")
    print(f"Rows returned: {len(result['rows'])}")
    print(f"\nAnswer: {result['summary']}")
