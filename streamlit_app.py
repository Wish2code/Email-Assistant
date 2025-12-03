import streamlit as st
import os
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# --- EmailState Definition ---
class EmailState(TypedDict):
    email: Dict[str, Any]
    email_category: Optional[str]
    spam_reason: Optional[str]
    is_spam: Optional[bool]
    email_draft: Optional[str]
    messages: List[Dict[str, Any]]

# --- LLM Initialization ---
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") 
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY missing in env or secrets.toml")
os.environ["GOOGLE_API_KEY"] = api_key

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)


def read_email(state: EmailState):
    email = state["email"]
    st.write(f"Alfred is processing an email from {email['sender']} with subject: {email['subject']}")
    return {}

def classify_email(state: EmailState):
    email = state["email"]
    prompt = f"""
    As Alfred the butler, analyze this email and determine if it is spam or legitimate.

    Email:
    From: {email['sender']}
    Subject: {email['subject']}
    Body: {email['body']}

    First, determine if this email is spam. If it is spam, explain why and start your explanation with "Reason:".
    If it is legitimate, categorize it (inquiry, complaint, thank you, request, information).
    """
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    response_text = response.content.lower()
    is_spam = "spam" in response_text and "not spam" not in response_text

    spam_reason = None
    if is_spam:
        try:
            spam_reason = response_text.split("reason:")[1].strip()
        except IndexError:
            spam_reason = "No specific reason provided by LLM."

    email_category = None
    if not is_spam:
        categories = ["inquiry", "complaint", "thank you", "request", "information"]
        for category in categories:
            if category in response_text:
                email_category = category
                break
        if not email_category:
            email_category = "uncategorized legitimate"

    new_messages = state.get("messages", []) + [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response.content}
    ]
    return {
        "is_spam": is_spam,
        "spam_reason": spam_reason,
        "email_category": email_category,
        "messages": new_messages
    }

def handle_spam(state: EmailState):
    
    st.warning(f"Alfred has marked the email as spam. Reason: {state['spam_reason']}")
    st.info("The email has been moved to the spam folder.")
    return {}

def draft_response(state: EmailState):
    email = state["email"]
    category = state["email_category"] or "general"
    prompt = f"""
    As Alfred the butler, draft a polite preliminary response to this email.

    Email:
    From: {email['sender']}
    Subject: {email['subject']}
    Body: {email['body']}

    This email has been categorized as: {category}

    Draft a brief, professional response that Mr. Ngaatendwe can review and personalize before sending.
    """
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    new_messages = state.get("messages", []) + [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response.content}
    ]
    return {
        "email_draft": response.content,
        "messages": new_messages
    }

def notify_mr_ngaatendwe(state: EmailState):
    email = state["email"]
    st.subheader(f"Email from {email['sender']}")
    st.write(f"Subject: {email['subject']}")
    st.write(f"Category: {state['email_category']}")
    st.text_area(
        "Draft Response:",
        value=state["email_draft"],
        height=200,
        key="notify_draft_response",
    )
    return {}

def route_email(state: EmailState) -> str:
    if state["is_spam"]:
        return "spam"
    else:
        return "legitimate"

# --- LangGraph Setup---
email_graph = StateGraph(EmailState)
email_graph.add_node("read_email", read_email)
email_graph.add_node("classify_email", classify_email)
email_graph.add_node("handle_spam", handle_spam)
email_graph.add_node("draft_response", draft_response)
email_graph.add_node("notify_mr_ngaatendwe", notify_mr_ngaatendwe)

email_graph.add_edge(START, "read_email")
email_graph.add_edge("read_email", "classify_email")
email_graph.add_conditional_edges(
    "classify_email",
    route_email,
    {
        "spam": "handle_spam",
        "legitimate": "draft_response"
    }
)
email_graph.add_edge("handle_spam", END)
email_graph.add_edge("draft_response", "notify_mr_ngaatendwe")
email_graph.add_edge("notify_mr_ngaatendwe", END)

compiled_graph = email_graph.compile()

# --- Streamlit UI ---
st.title("Ngaatendwe's Email Assistant")

sender = st.text_input("Sender's Email", "john.doe@example.com")
subject = st.text_input("Subject", "Important Inquiry")
body = st.text_area(
    "Email Body",
    "Dear Mr. Ngaatendwe, I have a question regarding...",
    key="email_body_input",
)

if st.button("Process Email"):
    initial_state = {
        "email": {"sender": sender, "subject": subject, "body": body},
        "is_spam": None,
        "spam_reason": None,
        "email_category": None,
        "email_draft": None,
        "messages": []
    }
    
    with st.spinner("Alfred is processing your email..."):
        final_state = compiled_graph.invoke(initial_state)
    
    st.subheader("Processing Result")
    if final_state["is_spam"]:
        st.error(f"This email was marked as SPAM. Reason: {final_state['spam_reason']}")
    else:
        st.success(f"This email is legitimate. Category: {final_state['email_category']}")
        # st.text_area(
        #     "Draft Response:",
        #     value=final_state["email_draft"],
        #     height=200,
        #     key="result_draft_response",
        # )
