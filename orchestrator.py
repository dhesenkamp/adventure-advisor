from base_agent import BaseAgent
from typing import Dict, Any, List
from dataclasses import dataclass
import ast
from langchain.prompts import ChatPromptTemplate

ROUTING_PROMPT = (
    "You are an intelligent router for an Adventure Advisor system. Your goal is to help users find suitable outdoor activities."
    " You will analyze the user's input and decide which specialized sub-agents to call based on the input provided."
    "Current input: {input}\n\n"
    "AVAILABLE AGENTS:"
    "- calendar: Check user's schedule, availability for specific dates"
    "- weather: Get weather forecasts for locations and dates"
    "- database: Query outdoor activities database (hiking, biking, etc)"
    "ROUTING LOGIC:"
    "1. If user mentions dates/times → include 'calendar'"
    "2. If user mentions weather concerns or outdoor activities → include 'weather' "
    "3. If user asks for activity recommendations → always include 'database'"
    "4. If you have incomplete info for good recommendations → ask clarifying questions"
    "Return your decision as a Python list with only the names of the agents to call, e.g. ['calendar', 'weather']."
    "If no agents are needed, return an empty list."
)
SUMMARY_PROMPT = (
    "You are a helpful Adventure Advisor assistant. Create a natural, conversational response."

    "USER QUERY: {input}"
    "AGENT DATA: {agentOutput}"

    "RESPONSE GUIDELINES:"
    "1. Be conversational and helpful"
    "2. If recommending activities, explain why they're good fits"
    "3. Include relevant weather/calendar considerations"
    "4. If info is missing, ask specific follow-up questions"
    "5. Acknowledge previous conversation context"

    "Create a natural response that helps the user plan their outdoor adventure."
)


@dataclass
class ConversationContext:
  userPreferences: Dict[str, Any]
  gatheredInfo: Dict[str, Any]
  pendingClarifications: List[str]
  lastActivitySuggestions: List[Dict[str, Any]]


class Orchestrator(BaseAgent):

  def __init__(self, apiKey: str, tools: list = list(), promptTemplate: str = None, agents: None | dict = None):
    """Initialize the Orchestrator agent with the provided API key, tools, and prompt template.

    Args:
      apiKey (str): The API key for the Gemini API.
      tools (list, optional): A list of tools to be used by the agent. Defaults to None.
      promptTemplate (str, optional): The prompt template for the agent. Defaults to None.
    """
    super().__init__(apiKey=apiKey, tools=tools, promptTemplate=promptTemplate)

    self.agents = agents
    self.context = ConversationContext({}, {}, [], [])

    # self.routingPrompt = self._buildPrompt(ROUTING_PROMPT)
    # self.reasoningPrompt = self._buildPrompt()
    # self.summaryPrompt = self._buildPrompt(SUMMARY_PROMPT)

  def routing(self, query: str) -> list:
    """Route the query to the appropriate agent(s) based on the input text."""

    prompt = ChatPromptTemplate.from_template(ROUTING_PROMPT)
    prompt = prompt.format_messages(input=query)
    response = self.llm.invoke(prompt)
    # Expecting something like: '["calendar"]' or '["calendar", "weather"]'

    try:
      parsed = ast.literal_eval(response.content)
      if isinstance(parsed, list):
        return parsed
      elif isinstance(response.content, str):
        return response.content
    except (SyntaxError, ValueError) as e:
      return []

  def callAgents(self, query: str, selectedAgents: list) -> str:
    """Handle the query by routing it to the appropriate agent(s) and returning the result."""
    results = list()

    for agent in selectedAgents:
      if agent in self.agents:
        result = self.agents[agent].run(query)
        results.append(result.get("output"))

    return "\n\n".join(results)

  def summarize(self, userQuery: str, result: str) -> str:
    """Aggregate the results from the selected agents into a single natural language response."""

    instructions = ChatPromptTemplate.from_template(
        SUMMARY_PROMPT
    )
    instructions = instructions.format_messages(
        input=userQuery,
        agentOutput=result
    )

    finalResponse = self.llm.invoke(instructions)
    return finalResponse.content if isinstance(finalResponse.content, str) else str(finalResponse.content)

  def run(self, query: str) -> str:
    """Run the orchestrator agent with a user query. The query is passed to the LLM, which decides which specialized agents to call.
    The results from the selected agents are aggregated and summarized into a single response.
    The final response is returned as a string.
    """

    selectedAgents = self.routing(query)
    if not isinstance(selectedAgents, list) or not selectedAgents:
      results = ""
    else:
      results = self.callAgents(query, selectedAgents)
    summary = self.summarize(query, results)

    return summary
