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

    # Call orchestrator logic here
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
    st.write("Currently only handles weather queries. Other queries will still yield an answer from the orchestrator LLM, but no further logic has been implemented. Also, the current logic is a bit sloppy and incomplete. Orchestrator doesn't have memory/context yet.")
    st.write("Example: 'What's the weather like in Trento, Italy tomorrow at 2pm?'")

    with st.sidebar:
      st.header("About")
      st.write("Available agents:")
      for agent in self.orchestrator.agents:
        st.write(f"- {agent}")

    self.renderChatHistory()

    if userInput := st.chat_input("Ask me about the weather..."):
      self.processUserInput(userInput)
