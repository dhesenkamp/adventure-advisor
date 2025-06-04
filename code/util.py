from agents.database import DatabaseAgent
from agents.calendar import CalendarAgent
from agents.weather import WeatherAgent
from agents.orchestrator.improved_orchestrator import ImprovedOrchestratorAgent
import os
import getpass
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
