from app.improved_streamlit import ImprovedStreamlitApp
from agents.database import DatabaseAgent
from agents.calendar import CalendarAgent
from agents.weather import WeatherAgent
from agents.orchestrator.improved_orchestrator import ImprovedOrchestratorAgent
import os
import getpass
import datetime
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the improved components


def setup_environment():
  if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter Gemini API key: ")

  api_key = os.environ.get("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY is required")

  return api_key


def initialize_agents(api_key: str) -> Dict[str, Any]:
  logger.info("Initializing agents")

  try:
    weather_agent = WeatherAgent(apiKey=api_key)
    logger.info("Weather agent initialized")
  except Exception as e:
    logger.error(f"Failed to initialize weather agent: {e}")
    weather_agent = None

  try:
    calendar_agent = CalendarAgent(apiKey=api_key)
    logger.info("Calendar agent initialized")
  except Exception as e:
    logger.error(f"Failed to initialize calendar agent: {e}")
    calendar_agent = None

  try:
    database_agent = DatabaseAgent(apiKey=api_key)
    logger.info("Database agent initialized")
  except Exception as e:
    logger.error(f"Failed to initialize database agent: {e}")
    database_agent = None

  agents = dict()
  if weather_agent:
    agents["weather"] = weather_agent
  if calendar_agent:
    agents["calendar"] = calendar_agent
  if database_agent:
    agents["database"] = database_agent

  if not agents:
    raise ValueError("No agents could be initialized")

  logger.info(
      f"Successfully initialized {len(agents)} agents: {list(agents.keys())}")
  return agents


def initialize_orchestrator(api_key: str, agents: Dict[str, Any]) -> ImprovedOrchestratorAgent:
  logger.info("Initializing orchestrator agent")

  try:
    orchestrator = ImprovedOrchestratorAgent(
        apiKey=api_key,
        agents=agents
    )
    logger.info("Orchestrator agent initialized successfully")
    return orchestrator
  except Exception as e:
    logger.error(f"Failed to initialize orchestrator: {e}")
    raise


def test_agents(orchestrator: ImprovedOrchestratorAgent):
  logger.info("Testing agent functionality")

  test_queries = [
      "What's the weather like today in Trento, Italy?",
      "Do I have any meetings tomorrow?",
      "Can you recommend a hiking trail for 3 hours around Lake Garda?"
  ]

  for query in test_queries:
    try:
      logger.info(f"Testing query: {query}")
      result = orchestrator.run(query)
      logger.info(f"Query successful. Response length: {len(result)}")
    except Exception as e:
      logger.error(f"Query failed: {e}")


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
