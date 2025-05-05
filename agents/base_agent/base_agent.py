import os
import getpass

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI


class BaseAgent:
  def __init__(self, apiKey: str, tools: list = list(), promptTemplate: str | None = None):
    """"Agent base class using the LangChain API. 
    Args:
        apiKey (str): API key for the LLM model, default is Google's Gemini
        tools (list): List of custom tools to be bound to the agent. Need to be decorated with @tool.
        promptTemplate (str | None): Custom prompt template for the agent. If None, a simple default template is used.
    """

    self.apiKey = apiKey
    self.model = self._loadModel()
    self.tools = tools
    self.prompt = self._buildPrompt(promptTemplate)
    self.agent = create_tool_calling_agent(self.model, self.tools, self.prompt)
    self.executor = AgentExecutor(
        agent=self.agent, tools=self.tools, verbose=True)

  def _loadModel(self) -> ChatGoogleGenerativeAI:
    """Load a specific model using LangChain wrapper. Model parameters can be changed here."""

    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        api_key=self.apiKey
    )

  def _buildPrompt(self, promptTemplate: str | None) -> ChatPromptTemplate:
    """Build a prompt template for the agent using the LangChain wrapper. A simple default template is used if no custom template is provided."""

    if promptTemplate is None:
      promptTemplate = (
          f"""Answer the user: {{input}}
          
          Your scratchpad: {{agent_scratchpad}}
          """
      )
    return ChatPromptTemplate.from_template(
        promptTemplate
    )

  def run(self, query: str) -> dict:
    """Run agent with a user query. The query is passed to the LLM and the result is returned as a dict. Get the NL result with key "output" and the tool call with the key "tool_call".

    Example output:
    """
    return self.executor.invoke({"input": query})


if __name__ == "__main__":
  if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter Gemini API key: ")

  executor = BaseAgent(
      apiKey=os.environ["GEMINI_API_KEY"]
  )

  query = "Hello world"
  result = executor.run(query)
  print(result)
