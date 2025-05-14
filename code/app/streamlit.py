import streamlit as st


class StreamlitApp:

  def __init__(self, orchestrator):
    self.orchestrator = orchestrator

  def run(self):
    st.title("Adventure Advisor")
    query = st.text_input("Ask me something (e.g., weather or appointments):")

    if st.button("Submit") and query:
      with st.spinner("Thinking..."):
        try:
          response = self.orchestrator.run(query)
          st.success("Response:")
          st.markdown(response["output"] if isinstance(
              response, dict) else response)
        except Exception as e:
          st.error(f"Error: {e}")
