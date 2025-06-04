import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import streamlit as st
import argparse
import base64

from database_agent import queryDatabase

CONFIG_DIR = "user_config"
BG_IMAGE = "antonella-messaglia.png"

# take a username as arg from the command line


def parse_args():
  parser = argparse.ArgumentParser(
      description="Adventure Advisor Streamlit App")
  parser.add_argument("--username", type=str, default="User",
                      help="Username for the session")
  return parser.parse_args()


class StreamlitApp:

  def __init__(self, orchestrator, user):

    st.set_page_config(page_title="Adventure Advisor",
                       page_icon="⛰", layout="wide")

    self.orchestrator = orchestrator
    self.user = user
    self._initializeSessionState()

  def _initializeSessionState(self):
    if "chatHistory" not in st.session_state:
      st.session_state.chatHistory = []

    config = self.loadConfig()
    if config:
      st.session_state.userPreferences = config
    else:
      st.session_state.userPreferences = {
          "name": f"{self.user}".capitalize(),
          "age": None,
          "distanceKm": 1,
          "durationHours": 1,
          "difficulty": 1,
          "preferredActivities": ["Hiking"],
          "location": "Trento"
      }

  def loadConfig(self):
    file = f"{CONFIG_DIR}/{self.user}.json"
    try:
      with open(file, "r") as f:
        return json.load(f)
    except FileNotFoundError:
      return {}

  def saveConfig(self, config):
    filename = f"{CONFIG_DIR}/{self.user}.json"
    with open(filename, "w") as f:
      json.dump(config, f, indent=2)

  def updateConfig(self, config, new_config):
    config.update(new_config)
    self.saveConfig(config)

  def imgToBase64(self, imgPath: str) -> str:
    with open(imgPath, "rb") as f:
      imgFile = f.read()
      return base64.b64encode(imgFile).decode()

  def renderSidebar(self):
    st.sidebar.header(
        f"Welcome back, {st.session_state.userPreferences.get("name", "User")}!")
    with st.sidebar.form("preferences_form"):

      st.session_state.userPreferences["distanceKm"] = st.slider(
          "🚶 Distance (km)", 1, 100,
          st.session_state.userPreferences["distanceKm"],
          help="Maximum distance you're willing to travel"
      )

      st.session_state.userPreferences["durationHours"] = st.slider(
          "⏱️ Duration (hours)", 1, 12,
          st.session_state.userPreferences["durationHours"],
          help="How long you want the activity to last"
      )

      st.session_state.userPreferences["difficulty"] = st.slider(
          "💪 Difficulty (1-5)", 1, 5,
          st.session_state.userPreferences["difficulty"],
          help="1=Very Easy, 2=Easy, 3=Moderate, 4=Hard, 5=Very Hard"
      )

      st.session_state.userPreferences["location"] = st.text_input(
          "📍 Location", st.session_state.userPreferences["location"]
      )

      activities = ["Hiking", "Cycling", "Running", "Climbing", "Skiing"]
      st.session_state.userPreferences["preferredActivities"] = st.multiselect(
          "🎯 Preferred Activities", activities,
          default=st.session_state.userPreferences["preferredActivities"]
      )

      submit_button = st.form_submit_button("Update Preferences")
      if submit_button:
        self.updateConfig(
            st.session_state.userPreferences,
            {
                "distanceKm": st.session_state.userPreferences["distanceKm"],
                "durationHours": st.session_state.userPreferences["durationHours"],
                "difficulty": st.session_state.userPreferences["difficulty"],
                "location": st.session_state.userPreferences["location"],
                "preferredActivities": st.session_state.userPreferences["preferredActivities"]
            }
        )
        st.success("Preferences updated!")

      with st.popover("Change user"):
        st.markdown("")
        changeUser = st.text_input(
            "What's your name?")
        if changeUser:
          st.session_state.userPreferences["name"] = changeUser.capitalize()
          self.loadConfig()

  def renderBackground(self):
    img = self.imgToBase64("assets/" + BG_IMAGE)
    bg = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpg;base64,{img}");
    background-size: cover;
    }}
    [data-testid="stHeader"] {{
    background-color: rgba(0, 0, 0, 0);
    }}
    [data-testid="stBottom"] > div {{
    background-color: rgba(0, 0, 0, 0);
    }}
    </style>
    """
    st.markdown(bg, unsafe_allow_html=True)

  def renderMainChat(self):
    for i, msg in enumerate(st.session_state.chatHistory):
      with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧗"):
        st.markdown(msg["content"])

    # Chat input

    if userQuery := st.chat_input("Ask me anything about outdoor activities!"):
      st.session_state.chatHistory.append(
          {"role": "user", "content": userQuery})

      with st.chat_message("user", avatar="🧗"):
        st.markdown(userQuery)

      self.generateResponse(userQuery)

  def generateResponse(self, query: str):
    with st.chat_message("assistant", avatar="🤖"):
      with st.spinner("🤔 Thinking..."):

        response = self.orchestrator.run(query)

        response_placeholder = st.empty()
        streamed_response = ""

        for char in response:
          streamed_response += char
          response_placeholder.markdown(streamed_response + "▌")
          time.sleep(0.01)

        response_placeholder.markdown(streamed_response)

      st.session_state.chatHistory.append(
          {"role": "assistant", "content": response})

      st.rerun()

  def run(self):
    self.renderBackground()
    self.renderSidebar()

    st.markdown(
        "<h1 style='text-align:center; color:#fff'>⛰ Adventure Advisor</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center; color:#fff;opacity:.84; font-style:italic'>Your way to more adventures</p>",
        unsafe_allow_html=True
    )

    self.renderMainChat()
