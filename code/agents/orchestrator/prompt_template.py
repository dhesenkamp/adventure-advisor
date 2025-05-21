ROUTER_PROMPT = """
You are a router that decides which specialized agent should handle a user request.

Available agents:
- calendar: handles events, appointments, availability.
- weather: handles weather, forecasts, temperature, conditions.

Input: {input}

Decide smartly which agent(s) should respond. Also consider indirect requests.
Return a list of agent names from ["calendar", "weather"].
"""

SUMMARY_PROMPT = (
    "You are a helpful assistant. A user asked the following question: {question}"
    "You received the following information from specialized agents:\n\n"
    "{agent_outputs}\n\n"
    "Based on the information provided, answer the user in conversational and concise natural language."
)
