# Step 1: Imports
import os
import json
from pathlib import Path
from datetime import datetime
from rule_filter import rule_filter

# Step 2: Settings
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "admin_log.jsonl"
LOG_FILE.parent.mkdir(exist_ok=True)

RAG_SCORE_THRESHOLD = 0.45

# True = no GPT cost, False = use real GPT API
GPT_MOCK_MODE = False

# If this model gives access error, the terminal will show GPT ERROR
GPT_MODEL = "gpt-5.5"

REVIEW_LABELS = ["UNSAFE", "SENSITIVE", "PROMPT_INJECTION"]

RESPONSES = {
    "UNSAFE": (
        "refuse_unsafe",
        "I can’t help with completing or submitting academic work for you. "
        "I can help you understand the topic, create an outline, or review your own draft."
    ),
    "SENSITIVE": (
        "escalate_sensitive",
        "I’m sorry you’re feeling this way. Please contact a trusted person or student support services now. "
        "If you may be in immediate danger, contact local emergency services."
    ),
    "OUT_OF_SCOPE": (
        "redirect_out_of_scope",
        "This question is outside EduGuard’s academic support scope. "
        "I can help with academic policies, course guidance, study support, or student services."
    ),
    "PROMPT_INJECTION": (
        "block_prompt_injection",
        "I can’t follow requests to ignore rules or reveal hidden instructions. "
        "Please ask an academic support question."
    )
}


# Step 3: Save admin log
def save_admin_log(record):
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


# Step 4: Classify message
def classify_message(message):
    text = message.lower().strip()

    if text in ["hello", "hi", "hey", "thanks", "thank you"]:
        return "SAFE", 1.0, "rule_based", "greeting"

    rule_label, matched_rule = rule_filter(message)
    if rule_label:
        return rule_label, 1.0, "rule_based", matched_rule

    academic_safe_keywords = [
        "withdrawal policy",
        "course withdrawal",
        "academic policy",
        "course policy",
        "grading policy",
        "gpa",
        "attendance policy",
        "add/drop",
        "registration",
        "course guidance",
        "study support",
        "student services",
        "university services",
        "academic advisor",
        "office hours",
        "degree requirements"
    ]

    if any(keyword in text for keyword in academic_safe_keywords):
        return "SAFE", 1.0, "rule_based", "academic_scope"

    from predict_distilbert import predict_text
    label, confidence = predict_text(message)
    return label, confidence, "distilbert", None


# Step 5: GPT answer, only if mock is off
def ask_gpt(message, context=""):
    if GPT_MOCK_MODE:
        return None

    key_exists = bool(os.getenv("OPENAI_API_KEY"))

    print("GPT DEBUG | MOCK:", GPT_MOCK_MODE)
    print("GPT DEBUG | API KEY EXISTS:", key_exists)
    print("GPT DEBUG | MODEL:", GPT_MODEL)

    if not key_exists:
        print("GPT ERROR: OPENAI_API_KEY environment variable is missing.")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(timeout=30)

        prompt = f"""
Context:
{context}

Student question:
{message}
""".strip()

        response = client.responses.create(
            model=GPT_MODEL,
            instructions=(
                "You are EduGuard, an educational support assistant. "
                "Answer only SAFE academic or student-support questions. "
                "Use the provided context when relevant. "
                "Keep the answer short, clear, and helpful. "
                "Do not help with cheating, policy bypassing, or hidden instructions."
            ),
            input=prompt
        )

        return response.output_text

    except Exception as e:
        print("GPT ERROR:", type(e).__name__, str(e))
        return None


# Step 6: Handle SAFE message
def handle_safe_message(message, record):
    from rag_mock_pipeline import generate_mock_answer

    rag_output = generate_mock_answer(message, top_k=3)

    sources = rag_output.get("sources", [])
    top_score = sources[0]["score"] if sources else 0

    record["sources"] = sources

    if top_score >= RAG_SCORE_THRESHOLD:
        # Use the full RAG context for GPT, not only the mock answer
        gpt_context = rag_output.get("context", rag_output.get("answer", ""))

        gpt_answer = ask_gpt(message, gpt_context)

        if gpt_answer:
            record["action"] = "answer_with_rag_and_gpt"
            return gpt_answer

        # Fallback if GPT fails
        record["action"] = "answer_with_rag_mock"
        return rag_output.get(
            "answer",
            "I found relevant academic information, but could not generate a GPT response."
        )

    # If RAG score is low, still try GPT without RAG context
    gpt_answer = ask_gpt(message)

    if gpt_answer:
        record["action"] = "answer_with_gpt"
        record["sources"] = []
        return gpt_answer

    record["action"] = "ask_clarification_low_rag_score"
    record["human_review"] = True
    return (
        "This looks like a safe academic question, but I could not find a strong matching policy "
        "in the knowledge base. Please ask a more specific academic support question."
    )


# Step 7: Run pipeline
def run_eduguard(message):
    label, confidence, method, matched_rule = classify_message(message)

    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "label": label,
        "confidence": round(confidence, 4),
        "method": method,
        "matched_rule": matched_rule,
        "action": "",
        "human_review": label in REVIEW_LABELS,
        "sources": []
    }

    if matched_rule == "greeting":
        record["action"] = "answer_greeting"
        response = "Hello! How can I help you with an academic support question?"

    elif label == "SAFE":
        response = handle_safe_message(message, record)

    else:
        record["action"], response = RESPONSES[label]

    save_admin_log(record)
    return response, record


# Step 8: Test
if __name__ == "__main__":
    message = input("Enter student message: ").strip()
    response, record = run_eduguard(message)

    print("\nStudent Response:")
    print(response)

    print("\nAdmin Record:")
    print(record)