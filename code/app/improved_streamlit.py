import time
import json
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any

from agents.database.tools import queryDatabase


class ImprovedStreamlitApp:

  def __init__(self, orchestrator):
    self.orchestrator = orchestrator
    self._initializeSessionState()

  def _initializeSessionState(self):
    if "chatHistory" not in st.session_state:
      st.session_state.chatHistory = []

    if "userPreferences" not in st.session_state:
      st.session_state.userPreferences = {
          "distanceKm": 15,
          "durationHours": 4,
          "difficulty": 2,
          "preferredActivities": ["Hiking"],
          "location": "Trento"
      }

    if "conversationContext" not in st.session_state:
      st.session_state.conversationContext = {}

    if "lastRecommendations" not in st.session_state:
      st.session_state.lastRecommendations = []

  def run(self):
    st.set_page_config(
        page_title="Adventure Advisor",
        page_icon="🏔️",
        layout="wide"
    )

    st.title("🏔️ Adventure Advisor")
    st.markdown("*Your AI-powered outdoor activity companion*")

    # Layout: sidebar and main content
    with st.sidebar:
      self.renderSidebar()

    # Main chat interface
    self.renderMainChat()

    # Show conversation context (for debugging)
    if st.checkbox("Show Conversation Context (Debug)", value=False):
      self.render_debug_info()

  def renderSidebar(self):
    st.markdown("### ⚙️ Preferences")

    distance = st.slider(
        "🚶 Distance (km)",
        min_value=1, max_value=50,
        value=st.session_state.userPreferences["distanceKm"],
        step=1,
        help="Maximum distance you're willing to travel"
    )

    duration = st.slider(
        "⏱️ Duration (hours)",
        min_value=1, max_value=12,
        value=st.session_state.userPreferences["durationHours"],
        step=1,
        help="How long you want the activity to last"
    )

    difficulty = st.slider(
        "💪 Difficulty",
        min_value=1, max_value=5,
        value=st.session_state.userPreferences["difficulty"],
        step=1,
        help="1=Very Easy, 2=Easy, 3=Moderate, 4=Hard, 5=Very Hard"
    )

    activityOptions = [
        "Hiking", "Mountainbiking", "Trail running",
        "Alpine tour", "Climbing", "Cycling"
    ]
    preferredActivities = st.multiselect(
        "🎯 Preferred Activities",
        activityOptions,
        default=st.session_state.userPreferences.get(
            "preferredActivities", [])
    )

    location = st.text_input(
        "📍 Preferred Location/Region",
        value=st.session_state.userPreferences.get("location", ""),
        placeholder="e.g., Dolomites, Lake Garda, Trento"
    )

    # Update preferences when changed
    st.session_state.userPreferences.update({
        "distanceKm": distance,
        "durationHours": duration,
        "difficulty": difficulty,
        "preferredActivities": preferredActivities,
        "location": location
    })

    st.markdown("---")

    # Quick action buttons
    st.markdown("### 🚀 Quick Actions")
    if st.button("🗑️ Clear Conversation", type="secondary", use_container_width=True):
      self.clear_conversation()

  def renderMainChat(self):
    for i, msg in enumerate(st.session_state.chatHistory):
      with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    # Chat input
    if userQuery := st.chat_input("Ask me about outdoor activities, weather, or your schedule..."):
      self.handle_user_input(userQuery)

  def handle_user_input(self, userQuery: str):
    """Handle user input and generate response"""
    # Add user message to chat
    st.session_state.chatHistory.append(
        {"role": "user", "content": userQuery})

    with st.chat_message("user"):
      st.markdown(userQuery)

    # Generate and display response
    self.generateResponse(userQuery)

  def generateResponse(self, query: str):
    with st.chat_message("assistant"):
      with st.spinner("🤔 Thinking..."):
        # Update orchestrator context with user preferences
        self.update_orchestrator_context()

        response = self.orchestrator.run(query)

        # Stream the response
        response_placeholder = st.empty()
        streamed_response = ""

        for char in response:
          streamed_response += char
          response_placeholder.markdown(streamed_response + "▌")
          time.sleep(0.01)

        response_placeholder.markdown(streamed_response)

      # Add to chat history
      st.session_state.chatHistory.append(
          {"role": "assistant", "content": response})

      # Update conversation context
      st.session_state.conversationContext = self.orchestrator.get_conversation_summary()

      # Rerun to show action buttons
      st.rerun()

  def update_orchestrator_context(self):
    """Update orchestrator context with current user preferences"""
    self.orchestrator.context.userPreferences.update(
        st.session_state.userPreferences)

  def handle_more_options(self):
    """Handle request for more activity options"""
    query = "Can you show me more activity options similar to what you just recommended?"
    self.handle_user_input(query)

  def handle_weather_check(self):
    """Handle weather check for recommended activities"""
    query = "What's the weather forecast for these recommended activities?"
    self.handle_user_input(query)

  def handle_schedule_check(self):
    """Handle schedule check for recommended activities"""
    query = "When would be the best time to do these activities based on my schedule?"
    self.handle_user_input(query)

  def clear_conversation(self):
    """Clear the conversation history"""
    st.session_state.chatHistory = []
    st.session_state.conversationContext = {}
    st.session_state.lastRecommendations = []

    # Also clear orchestrator memory
    self.orchestrator.memory.clear()
    self.orchestrator.context = type(self.orchestrator.context)(
        userPreferences={},
        gathered_info={},
        pending_clarifications=[],
        last_activity_suggestions=[]
    )

    st.rerun()

  def render_debug_info(self):
    """Render debug information"""
    st.markdown("### 🔍 Debug Information")

    with st.expander("User Preferences"):
      st.json(st.session_state.userPreferences)

    with st.expander("Conversation Context"):
      st.json(st.session_state.conversationContext)

    with st.expander("Orchestrator Context"):
      if hasattr(self.orchestrator, 'context'):
        st.json(self.orchestrator.context.__dict__)

    with st.expander("Chat History"):
      for i, msg in enumerate(st.session_state.chatHistory):
        st.write(
            f"**{i+1}. {msg['role'].title()}:** {msg['content'][:100]}...")

  def render_activity_cards(self, activities: list):
    """Render activity recommendation cards"""
    if not activities:
      return

    st.markdown("### 🎯 Recommended Activities")

    for activity in activities:
      with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
          st.markdown(f"**{activity.get('title', 'Unknown Activity')}**")
          st.markdown(f"📍 {activity.get('location', 'Unknown location')}")

        with col2:
          difficulty_stars = "⭐" * activity.get('difficulty', 1)
          st.markdown(f"**Difficulty:** {difficulty_stars}")

        with col3:
          length_km = activity.get('length', 0) / \
              1000 if activity.get('length') else 0
          st.markdown(f"**Distance:** {length_km:.1f} km")

        st.markdown("---")
