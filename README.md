# Ngaatendwe's Email Assistant (Alfred)

An agent that uses **LangGraph**, **LangChain**, and **Google Gemini** to process incoming emails. The app:

- Reads a user-provided email (sender, subject, body).
- Uses an LLM to classify the email as **spam** or **legitimate**.
- If spam, shows the reason and marks it as spam.
- If legitimate, categorizes it (inquiry, complaint, thank you, request, information).
- Drafts a polite response for Mr. Ngaatendwe to review.
- Shows the draft in the UI for further editing.

---

## Tech Stack

- Python
- [Streamlit](https://streamlit.io/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://python.langchain.com/)
- [Google Gemini via langchain-google-genai](https://python.langchain.com/docs/integrations/llms/google_generative_ai/)

Main app file: `streamlit_app.py`

---

## Prerequisites

- Python 3.9+ installed
- A Google Generative AI (Gemini) API key

Set the API key in your environment (or via a `.env` file):

```bash
# .env
GOOGLE_API_KEY=your_api_key_here
```

The app will load this via `python-dotenv` and also checks `secrets.toml` if you run it on Streamlit Cloud.

---

## Installation

From the project root (`c:\Users\12\Documents\LangGraph Agent`):

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# then:
pip install streamlit langgraph langchain-core langchain-google-genai python-dotenv
```

(Adjust package names/versions as needed, depending on your environment.)

---

## Running the App

From the same project directory:

```bash
streamlit run streamlit_app.py
```

This will open (or print a URL to) the Streamlit UI in your browser.

---

## How It Works

### State

The app defines an `EmailState` (a `TypedDict`) that tracks:

- `email`: `{ sender, subject, body }`
- `email_category`: category for legitimate emails
- `spam_reason`: explanation if classified as spam
- `is_spam`: boolean
- `email_draft`: drafted response text
- `messages`: history of prompts/responses sent to the LLM

### Graph Nodes (LangGraph)

The LangGraph workflow in `streamlit_app.py`:

1. **read_email**
   - Reads the email from the current state.
   - Displays a message in Streamlit that Alfred is processing the email.

2. **classify_email**
   - Prompts the Gemini model to:
     - Decide if the email is spam or not.
     - If spam, return a reason (prefixed with `"Reason:"`).
     - If legitimate, categorize as: `inquiry`, `complaint`, `thank you`, `request`, `information` (or `uncategorized legitimate`).
   - Updates `is_spam`, `spam_reason`, `email_category`, and `messages`.

3. **route_email** (conditional edges)
   - If `is_spam` is `True`, route to `handle_spam`.
   - Otherwise, route to `draft_response`.

4. **handle_spam**
   - Displays a Streamlit warning and info message explaining that the email is spam and moved to spam folder.

5. **draft_response**
   - Uses Gemini to draft a polite response, based on the email and the derived category.
   - Updates `email_draft` and `messages`.

6. **notify_mr_ngaatendwe**
   - Shows:
     - Sender
     - Subject
     - Category
     - A text area with the drafted response so it can be reviewed and edited.

The graph is wired using:

- `add_node`, `add_edge`, `add_conditional_edges`
- Then compiled with `email_graph.compile()` and invoked once when the user clicks **"Process Email"**.

---

## Streamlit UI

The UI in `streamlit_app.py`:

- Title: **"Ngaatendwe's Email Assistant"**
- Inputs:
  - Sender's Email (`st.text_input`)
  - Subject (`st.text_input`)
  - Email Body (`st.text_area`)
- Button: **"Process Email"**
  - Creates the initial `EmailState`
  - Invokes the compiled LangGraph
  - Displays:
    - If spam: an error with the spam reason.
    - If legitimate: success message with the category.
    - The node `notify_mr_ngaatendwe` already shows the draft response text area.

---

## Configuration and Customization

- **Model**: change the Gemini model or temperature here:

  ```python
  model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
  ```

- **Categories**: modify the list of categories in `classify_email` to support your own taxonomy.
- **Prompts**: adjust the classification and drafting prompts to change Alfred’s style or behavior.
- **Spam Logic**: currently, `is_spam` is detected by checking if `"spam"` appears in the response text and `"not spam"` does not. You can replace this with a more structured parsing strategy if desired.

---

## Folder Structure

Minimal expected structure:

```text
c:\Users\...\Email-Agent
├─ streamlit_app.py
└─ README.md
```

(You can add `requirements.txt`, `.env`, or other standard project files as needed.)

---
