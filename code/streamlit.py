import streamlit as st


class Streamlit:
  def __init__(self):
    st.title("ChatGPT")
    st.write("This is a simple ChatGPT web app.")
    self.input_text = st.text_input("You: ", "")
    self.output_text = st.empty()
    self.button = st.button("Send")

  def run(self):
    if self.button and self.input_text:
      self.output_text.text(f"ChatGPT: {self.input_text}")
      self.input_text = ""


if __name__ == "__main__":
  app = Streamlit()
