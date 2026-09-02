import os
import requests
import streamlit as st

st.set_page_config(page_title="Nova | CloudDesk Support", page_icon="💬")
st.title("Nova")
st.caption("CloudDesk Customer Support Copilot")
st.info("Hi! I’m Nova. I can help with your CloudDesk account, billing, subscriptions, integrations, API issues, and technical problems.")
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
st.session_state.setdefault("conversation_id", None)
st.session_state.setdefault("messages", [])

with st.sidebar:
    st.subheader("Support metrics")
    try:
        metrics = requests.get(f"{backend_url}/metrics", timeout=10).json()
        st.metric("Total conversations", metrics["total_conversations"])
        st.metric("AI resolution rate", f"{metrics['ai_resolution_rate']:.0%}")
        st.metric("Escalation rate", f"{metrics['escalation_rate']:.0%}")
        st.metric("Avg response time", f"{metrics['average_response_time_ms']:.0f} ms")
        feedback_score = metrics["customer_feedback_score"]
        st.metric("Feedback score", f"{feedback_score:.0%}" if feedback_score is not None else "No feedback yet")
        st.metric("Retrieval failures", metrics["knowledge_base_retrieval_failures"])
        if metrics["intent_distribution"]:
            with st.expander("Intent distribution"):
                st.write(metrics["intent_distribution"])
    except requests.RequestException:
        st.caption("Metrics unavailable - backend not reachable.")

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.write(item["content"])
        if item["role"] == "assistant" and item.get("sources"):
            with st.expander("CloudDesk knowledge used"):
                st.write(item["sources"])

message = st.chat_input("Describe your CloudDesk support issue")
if message:
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.write(message)
    with st.chat_message("assistant"):
        with st.spinner("Searching verified CloudDesk guidance…"):
            try:
                response = requests.post(f"{backend_url}/chat", json={"message": message, "conversation_id": st.session_state.conversation_id}, timeout=30)
                response.raise_for_status()
                data = response.json()
                st.session_state.conversation_id = data["conversation_id"]
                st.session_state.messages.append({"role": "assistant", "content": data["answer"], "sources": data["sources"], "query_id": data["query_id"]})
                if data["escalated"]:
                    st.warning(f"Escalation created: {data['escalation_reason']}")
                elif data.get("needs_clarification"):
                    st.info("Nova needs a bit more detail before answering confidently.")
                st.write(data["answer"])
                if data["sources"]:
                    with st.expander("CloudDesk knowledge used"):
                        st.write(data["sources"])
                left, right = st.columns(2)
                for column, label, helpful in ((left, "👍 Helpful", True), (right, "👎 Not helpful", False)):
                    if column.button(label, key=f"feedback-{data['query_id']}-{helpful}"):
                        result = requests.post(f"{backend_url}/feedback", json={"query_id": data["query_id"], "helpful": helpful}, timeout=10)
                        result.raise_for_status()
                        st.toast("Thanks — your feedback has been recorded.")
            except requests.RequestException as exc:
                st.error(f"Could not reach the support service: {exc}")
