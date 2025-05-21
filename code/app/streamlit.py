import time
import streamlit as st

from agents.database.tools import queryDatabase


class StreamlitApp:

  def __init__(self, orchestrator):
    self.orchestrator = orchestrator
    self.difficulty = 2
    self.durationMin = 120
    self.category = "Hiking"

    # self.randomActivities = queryDatabase.invoke({
    #     "category": "Hiking",
    #     "difficulty": 2,
    #     "duration_min": 60,
    #     "limit": 1
    # })

  def run(self):
    # Initialize session state for chat history
    if "chatHistory" not in st.session_state:
      st.session_state.chatHistory = []  # Stores full conversation

    st.title("quickstart")
    with st.sidebar:
      st.markdown(
          """
          ### Available agents
          - **Weather Agent**: Provides weather information.
          - **Calendar Agent**: Manages calendar events and appointments.
          - **Database Agent**: Interacts with a database for data retrieval and storage.
          """
      )
      st.subheader("Settings")
      st.slider(
          "Distance (km)", min_value=0, max_value=50,
          value=15, step=1, help="Adjust the distance for your activity.",
      )
      st.slider(
          "Duration (hours)", min_value=0, max_value=12,
          value=4, step=1, help="Adjust the duration for your activity.",
      )
      st.slider(
          "Difficulty", min_value=1, max_value=5,
          value=2, step=1, help="Adjust the difficulty for your activity. 1=easy, 5=hard.",
      )

    for msg in st.session_state.chatHistory:
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    if userQuery := st.chat_input("Say something"):
      st.session_state.chatHistory.append(
          {"role": "user", "content": userQuery})
      with st.chat_message("user"):
        st.markdown(userQuery)

      self.generateResponse(userQuery)

  def generateResponse(self, query):
    """Generate a response from the orchestrator agent."""

    with st.chat_message("assistant"):
      with st.spinner("Thinking..."):
        response = self.orchestrator.run(query)
        response = st.write_stream(self.chatStream(response))

      st.session_state.chatHistory.append(
          {"role": "assistant", "content": response}
      )

  def chatStream(self, response):
    for char in response:
      yield char
      time.sleep(.01)
