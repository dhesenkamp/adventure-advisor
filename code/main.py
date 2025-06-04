from app.improved_streamlit import ImprovedStreamlitApp
from agents.database import DatabaseAgent
from agents.calendar import CalendarAgent
from agents.weather import WeatherAgent
from agents.orchestrator.improved_orchestrator import ImprovedOrchestratorAgent
from util import setup_environment, initialize_agents, initialize_orchestrator, test_agents
import os
import getpass
import datetime
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the improved components


def main():
  print("🏔️  Starting Adventure Advisor...")

  try:
    api_key = setup_environment()
    agents = initialize_agents(api_key)
    orchestrator = initialize_orchestrator(api_key, agents)

    # Optional: Test agents
    if os.environ.get("TEST_AGENTS", "").lower() == "true":
      test_agents(orchestrator)

    logger.info("Starting Streamlit application")
    app = ImprovedStreamlitApp(orchestrator)
    app.run()

  except KeyboardInterrupt:
    logger.info("Application stopped by user")
  except Exception as e:
    logger.error(f"Application error: {e}")
    raise


def run_cli_mode():
  """Run in CLI mode for testing"""
  print("🏔️  Adventure Advisor - CLI Mode")

  try:
    api_key = setup_environment()
    agents = initialize_agents(api_key)
    orchestrator = initialize_orchestrator(api_key, agents)

    print("\nType 'quit' to exit, 'clear' to clear conversation history")
    print("Ask me about outdoor activities, weather, or your schedule!\n")

    while True:
      try:
        query = input("\n🏔️  You: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
          break
        elif query.lower() == 'clear':
          orchestrator.memory.clear()
          print("Conversation history cleared!")
          continue
        elif not query:
          continue

        print("🤖 Assistant:", end=" ")
        response = orchestrator.run(query)
        print(response)

      except KeyboardInterrupt:
        break
      except Exception as e:
        print(f"Error: {e}")

  except Exception as e:
    print(f"Failed to start CLI mode: {e}")


if __name__ == "__main__":
  import sys

  if len(sys.argv) > 1 and sys.argv[1] == "cli":
    run_cli_mode()
  else:
    main()


def create_sample_config():
  """Create a sample configuration file"""
  config = {
      "app": {
          "title": "Adventure Advisor",
          "debug": False,
          "test_agents": False
      },
      "agents": {
          "max_retries": 3,
          "timeout": 30
      },
      "streamlit": {
          "theme": "light",
          "sidebar_width": 300
      }
  }

  import json
  with open("config.json", "w") as f:
    json.dump(config, f, indent=2)

  print("Sample config.json created!")
