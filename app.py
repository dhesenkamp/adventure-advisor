import streamlit as st


class StreamlitApp:
  def __init__(self, orchestrator=None):
    self.orchestrator = orchestrator
    self._initSession()

  def _initSession(self):
    if "history" not in st.session_state:
      st.session_state.history = []

  def renderChatHistory(self):
    for msg in st.session_state.history:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

  def processUserInput(self, userInput):
    st.session_state.history.append({"role": "user", "content": userInput})

    # Call your orchestrator logic here
    if self.orchestrator:
      response = self.orchestrator.run(userInput)
    else:
      response = f"🤖 Orchestrator received: '{userInput}'"

    st.session_state.history.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
      st.markdown(response)

  def run(self):
    st.set_page_config(page_title="Adventure Advisor", page_icon="🥾")
    st.title("🥾 Adventure Advisor")

    self.renderChatHistory()

    if userInput := st.chat_input("Ask me anything..."):
      self.processUserInput(userInput)
