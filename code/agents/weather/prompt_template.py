from datetime import datetime

"""TODO
- information about the current day to handle relative dates (e.g. tomorrow, next week) -> possible with datetime?
- refine prompt
  - Return the result as a valid JSON object in this format:
    {{
        "action": "return_sql_query_results",
        "data": {{
            "query": "<PostgreSQL query here>",
            "query_response": [<array of rows as JSON objects>]
        }}
    }}
"""

PROMPT_TEMPLATE = (
    """
      Today is {today}.
      Extract the date and location from the {input} and convert the date to string YYYY-MM-DD format, then call the `getWeather` tool with the extracted date and location.
      Example:
      User: "What will the weather be like on 6th of June in Berlin?"
      → Extracted date: "2025-06-06"
      → Extracted location: "Berlin"
      → Call tool: getWeather(location="Berlin", date="2025-06-06")
      Look up the weather and give a forecast for the given day and location, using the getWeather tool. Use the users input to get the location and day.
      {agent_scratchpad}
      Return the result as a valid JSON object in this format:
      {{
        "action": "return_weather",
        "data": {{
          "date": "<actual date in YYYY-MM-DD>",
          "location": "<location>",
          "forecast": [<returned weather information>]
        }}
      }}
    """
)
