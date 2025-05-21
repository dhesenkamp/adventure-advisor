import ast

from langchain_core.prompts import ChatPromptTemplate

from agents.base_agent import BaseAgent
from agents.orchestrator.prompt_template import ROUTER_PROMPT, SUMMARY_PROMPT


class OrchestratorAgent(BaseAgent):
  """
  Specialized agent for routing requests to other specialized agents.
  """

  def __init__(self, apiKey, agents: dict):
    super().__init__(
        apiKey=apiKey,
    )
    self.agents = agents

  def routing(self, query: str) -> list:
    """Route the query to the appropriate agent(s) based on the input text."""

    prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
    prompt = prompt.format_messages(input=query)
    response = self.model.invoke(prompt)
    # Expecting something like: '["calendar"]' or '["calendar", "weather"]'

    if isinstance(response.content, str):
      return ast.literal_eval(response.content)
    return response.content

  def handle(self, query: str, selectedAgents: list) -> str:
    """Handle the query by routing it to the appropriate agent(s) and returning the result."""

    results = list()

    for agent in selectedAgents:
      if agent in self.agents:
        result = self.agents[agent].run(query)
        results.append(result.get("output"))

    return "\n\n".join(results)

  def summarize(self, user_query: str, result: str) -> str:
    """Aggregate the results from the selected agents into a single natural language response."""

    instructions = ChatPromptTemplate.from_template(
        SUMMARY_PROMPT
    )
    instructions = instructions.format_messages(
        question=user_query,
        agent_outputs=result
    )

    finalResponse = self.model.invoke(instructions)
    return finalResponse.content if isinstance(finalResponse.content, str) else str(finalResponse.content)

  def run(self, query: str) -> str:
    """Run the orchestrator agent with a user query. The query is passed to the LLM, which decides which specialized agents to call.
    The results from the selected agents are aggregated and summarized into a single response.
    The final response is returned as a string.
    """

    selectedAgents = self.routing(query)
    if not selectedAgents:
      return "No agents available to handle the request."
    results = self.handle(query, selectedAgents)
    summary = self.summarize(query, results)

    return summary
