import streamlit as st
from groq import Groq
from tavily import TavilyClient

# ------------------------------------------
# PAGE SETUP
# ------------------------------------------
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="centered"
)

# ------------------------------------------
# CUSTOM CSS — Clean Advanced Look
# ------------------------------------------
st.markdown("""
<style>
    /* Background */
    .stApp { background-color: #0f1117; }

    /* Title */
    h1 { 
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* Chat input */
    .stChatInput input {
        background: #1e2130 !important;
        border: 1px solid #6366f1 !important;
        color: white !important;
        border-radius: 12px !important;
    }

    /* User message */
    [data-testid="stChatMessageContent"] {
        background: #1e2130 !important;
        border-radius: 12px !important;
        border: 1px solid #2d3148 !important;
        color: #e2e8f0 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1a1d2e !important;
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100% !important;
    }

    /* Caption */
    .stCaption { color: #6366f1 !important; }

    /* Code blocks */
    code { 
        background: #1e2130 !important;
        color: #a5f3fc !important;
        border-radius: 6px !important;
    }

    pre {
        background: #1e2130 !important;
        border: 1px solid #2d3148 !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }

    /* Divider */
    hr { border-color: #2d3148 !important; }

    /* Metrics */
    [data-testid="stMetricValue"] { color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------
# API CLIENTS
# ------------------------------------------
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
tavily_client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

# ------------------------------------------
# SESSION STATE
# ------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = [
        {
            "role": "system",
            "content": """You are an expert AI assistant and coding helper.

RULES:
- Reply in English clearly and concisely
- For ANY code request, always use proper markdown code blocks with language specified like ```python, ```javascript etc
- Explain code step by step
- For latest news/current info, web search results will be provided — use them
- Remember everything the user tells you in the conversation
- Be friendly and professional"""
        }
    ]

if "search_count" not in st.session_state:
    st.session_state.search_count = 0

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.divider()

    # Stats
    total_msgs = len([m for m in st.session_state.history if m["role"] != "system"])
    user_msgs  = len([m for m in st.session_state.history if m["role"] == "user"])

    st.metric("💬 Total Messages", total_msgs)
    st.metric("🔍 Web Searches", st.session_state.search_count)
    st.metric("❓ Your Questions", user_msgs)

    st.divider()

    # Model info
    st.markdown("**🧠 Model**")
    st.caption("Llama 3.3 70B")

    st.markdown("**🌐 Search**")
    st.caption("Tavily Real-time")

    st.divider()

    # Reset
    if st.button("🔄 New Chat"):
        st.session_state.history = [
            {
                "role": "system",
                "content": """You are an expert AI assistant and coding helper.
Reply in English. For code, always use markdown code blocks.
Remember everything the user tells you."""
            }
        ]
        st.session_state.search_count = 0
        st.rerun()

    st.divider()
    st.caption("Made with ❤️ using Groq + Streamlit")

# ------------------------------------------
# MAIN CHAT UI
# ------------------------------------------
st.title("🤖 AI Assistant")
st.caption("Ask anything — code, questions, latest news!")

# Purane messages dikhao
for msg in st.session_state.history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])

# ------------------------------------------
# USER INPUT
# ------------------------------------------
sawaal = st.chat_input("Ask me anything... (code, news, questions)")

if sawaal:
    # User message dikhao
    with st.chat_message("user", avatar="👤"):
        st.markdown(sawaal)

    st.session_state.history.append({
        "role": "user",
        "content": sawaal
    })

    # Bot ka jawab
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                # Search keywords
                search_keywords = [
                    "latest", "current", "today", "news", "2024", "2025", "2026",
                    "price", "score", "weather", "who is", "recent", "update",
                    "live", "right now", "aaj", "abhi"
                ]

                needs_search = any(
                    word in sawaal.lower() for word in search_keywords
                )

                if needs_search:
                    with st.status("🔍 Searching the web...", expanded=False):
                        results = tavily_client.search(
                            query=sawaal,
                            max_results=3
                        )
                        web_info = ""
                        for r in results.get("results", []):
                            web_info += f"- {r['title']}: {r['content'][:300]}\n"

                    st.session_state.search_count += 1

                    search_msg = f"""User asked: {sawaal}

Web search results:
{web_info}

Answer based on these search results accurately."""

                    messages_to_send = st.session_state.history[:-1] + [
                        {"role": "user", "content": search_msg}
                    ]
                else:
                    messages_to_send = st.session_state.history

                # Groq API call
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_to_send,
                    max_tokens=1000
                )

                bot_reply = response.choices[0].message.content
                st.markdown(bot_reply)

                st.session_state.history.append({
                    "role": "assistant",
                    "content": bot_reply
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")