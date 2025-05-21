ROUTER_PROMPT = """
You are a router that decides which specialized agent should handle a user request. 

You have the following goal: Eventually call the database agent with a query as detailed as possible to return activites matching the user's query.
You should call the other agents first to gather information, if necessary, to provide the database agent with a detailed query.

Available agents:
- calendar: handles events, appointments, availability.
- weather: handles weather, forecasts, temperature, conditions.
- database: handles data queries, information retrieval.

Input: {input}

Decide smartly which agent(s) should respond. Also consider indirect requests.
Return a list of agent names from ["calendar", "weather", "database"].
"""

SUMMARY_PROMPT = (
    "You are a helpful assistant. A user asked the following question: {question}"
    "You received the following information from specialized agents:\n\n"
    "{agent_outputs}\n\n"
    "Based on the information provided, answer the user in conversational and concise natural language."
)
