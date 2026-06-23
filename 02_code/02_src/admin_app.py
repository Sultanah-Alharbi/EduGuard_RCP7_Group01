# Step 1: Import libraries
import json
from pathlib import Path
import pandas as pd
import streamlit as st

# Step 2: Define log file path
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "admin_log.jsonl"
LOG_FILE.parent.mkdir(exist_ok=True)

# Step 3: Configure Streamlit page
st.set_page_config(page_title="EduGuard Admin", page_icon="🔐", layout="wide")

# Step 4: Define label styles
STYLE = {
    "UNSAFE": {"name": "Unsafe Request", "icon": "🚫", "bg": "#fff1e6", "border": "#f97316"},
    "SENSITIVE": {"name": "Student Safety", "icon": "🚨", "bg": "#fde2e2", "border": "#ef4444"},
    "PROMPT_INJECTION": {"name": "Prompt Injection", "icon": "🛡️", "bg": "#f1e8ff", "border": "#8b5cf6"},
    "SAFE": {"name": "Safe", "icon": "✅", "bg": "#e9f9ee", "border": "#22c55e"},
    "OUT_OF_SCOPE": {"name": "Out of Scope", "icon": "↪️", "bg": "#fff7d6", "border": "#f59e0b"},
}

# Step 5: Define label explanations for tooltips and cards
LABEL_HELP = {
    "SAFE": "Academic support question that can be answered using RAG and GPT.",
    "UNSAFE": "Academic dishonesty or cheating request.",
    "SENSITIVE": "Student safety or wellbeing concern.",
    "OUT_OF_SCOPE": "Question not related to academic or university support.",
    "PROMPT_INJECTION": "Attempt to bypass system rules or reveal hidden prompts.",
}

# Step 6: Define crisis keywords for critical sensitive cases
CRISIS_KEYWORDS = [
    "hurt myself",
    "kill myself",
    "suicide",
    "self-harm",
    "end my life",
    "violence",
    "immediate danger",
    "emergency",
]

# Step 7: Add simple card style
st.markdown("""
<style>
.alert-card {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 12px;
    border-left: 7px solid;
}
</style>
""", unsafe_allow_html=True)

# Step 8: Load logs from JSONL file
def load_logs():
    if not LOG_FILE.exists():
        return []

    logs = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            logs.append(json.loads(line))

    return logs

# Step 9: Assign severity level based on label and message
def get_severity(row):
    label = row.get("label", "")
    message = str(row.get("message", "")).lower()

    if label in ["SAFE", "OUT_OF_SCOPE"]:
        return "LOW"

    if label == "UNSAFE":
        return "MEDIUM"

    if label == "PROMPT_INJECTION":
        return "HIGH"

    if label == "SENSITIVE":
        if any(keyword in message for keyword in CRISIS_KEYWORDS):
            return "CRITICAL"
        return "HIGH"

    return "LOW"

# Step 10: Prepare logs dataframe
def prepare_df(logs):
    df = pd.DataFrame(logs)

    if "method" not in df.columns:
        df["method"] = "unknown"

    if "matched_rule" not in df.columns:
        df["matched_rule"] = "None"

    if "human_review" not in df.columns:
        df["human_review"] = False

    if "sources" not in df.columns:
        df["sources"] = [[] for _ in range(len(df))]

    df["method"] = df["method"].fillna("unknown")
    df["matched_rule"] = df["matched_rule"].fillna("None")
    df["human_review"] = df["human_review"].fillna(False)
    df["severity"] = df.apply(get_severity, axis=1)

    return df

# Step 11: Show colored alert card
def show_card(row):
    style = STYLE.get(row["label"], STYLE["OUT_OF_SCOPE"])

    st.markdown(
        f"""
        <div class="alert-card" style="background:{style['bg']}; border-color:{style['border']};">
        <b>{style['icon']} {style['name']}</b><br><br>
        <b>Time:</b> {row['time']}<br>
        <b>Student Message:</b> {row['message']}<br>
        <b>Label:</b> {row['label']}<br>
        <b>Meaning:</b> {LABEL_HELP.get(row['label'], 'No description available.')}<br>
        <b>Severity:</b> {row['severity']}<br>
        <b>Confidence:</b> {row['confidence']}<br>
        <b>Method:</b> {row['method']}<br>
        <b>Matched Rule:</b> {row['matched_rule']}<br>
        <b>Action:</b> {row['action']}<br>
        <b>Status:</b> PENDING
        </div>
        """,
        unsafe_allow_html=True
    )

# Step 12: Sidebar
st.sidebar.title("🔐 EduGuard Admin")

if st.sidebar.button("Clear Admin Logs"):
    LOG_FILE.write_text("", encoding="utf-8")
    st.session_state.reviewed = []
    st.rerun()

# Step 13: Page title
st.title("🔐 EduGuard Admin Dashboard")
st.caption("Escalation log — internal monitoring only")

# Step 14: Load logs
logs = load_logs()

if not logs:
    st.info("No logs found yet.")

else:
    df = prepare_df(logs)

    # Step 15: Overview metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Total Alerts",
        len(df),
        help="Total number of requests logged by EduGuard."
    )

    col2.metric(
        "Review Needed",
        int(df["human_review"].sum()),
        help="Requests marked for human review."
    )

    col3.metric(
        "Unsafe",
        int((df["label"] == "UNSAFE").sum()),
        help=LABEL_HELP["UNSAFE"]
    )

    col4.metric(
        "Student Safety",
        int((df["label"] == "SENSITIVE").sum()),
        help=LABEL_HELP["SENSITIVE"]
    )

    col5.metric(
        "Prompt Injection",
        int((df["label"] == "PROMPT_INJECTION").sum()),
        help=LABEL_HELP["PROMPT_INJECTION"]
    )

    st.divider()

    # Step 16: Show high-risk alerts only
    st.subheader("High-Risk Alerts")

    high_risk = ["UNSAFE", "SENSITIVE", "PROMPT_INJECTION"]
    alerts = df[df["label"].isin(high_risk)].tail(8)

    if alerts.empty:
        st.success("No high-risk alerts.")
    else:
        for _, row in alerts[::-1].iterrows():
            show_card(row)

    st.divider()

    # Step 17: Show safety logs table
    st.subheader("Safety Logs")

    labels = ["ALL", "SAFE", "UNSAFE", "SENSITIVE", "OUT_OF_SCOPE", "PROMPT_INJECTION"]
    selected_label = st.selectbox("Filter by label", labels)

    table_df = df.copy()

    if selected_label != "ALL":
        table_df = table_df[table_df["label"] == selected_label]

    table_df = table_df[::-1]

    # Step 18: Add task done checkbox
    if "reviewed" not in st.session_state or len(st.session_state.reviewed) != len(df):
        st.session_state.reviewed = [False] * len(df)

    df["task_done"] = st.session_state.reviewed
    table_df["task_done"] = df.loc[table_df.index, "task_done"]

    columns = [
        "task_done",
        "time",
        "label",
        "severity",
        "confidence",
        "method",
        "matched_rule",
        "action",
        "message"
    ]

    # Step 19: Display editable review checkbox
    edited_df = st.data_editor(
        table_df[columns],
        hide_index=True,
        width="stretch",
        disabled=[
            "time",
            "label",
            "severity",
            "confidence",
            "method",
            "matched_rule",
            "action",
            "message"
        ],
        column_config={
            "task_done": st.column_config.CheckboxColumn(
                "Task Done ✅",
                help="Mark this request as reviewed."
            )
        }
    )

    # Step 20: Save completed review tasks
    for index, value in zip(table_df.index, edited_df["task_done"]):
        st.session_state.reviewed[index] = value

    st.write("Completed reviews:", int(sum(st.session_state.reviewed)))

    st.divider()

    # Step 21: Show latest request details
    st.subheader("Latest Request Details")

    latest = df.iloc[-1]
    show_card(latest)

    # Step 22: Show RAG sources if available
    if latest["sources"]:
        st.write("**RAG Sources:**")
        for source in latest["sources"]:
            st.write(
                "-",
                source["id"],
                "|",
                source["title"],
                "| score:",
                round(source["score"], 3)
            )