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
    """Look up the weather for the date and location given by the user input. Transform any date mentioned by the user into a date format YYYY-MM-DD.

    User input: {input}

    Your scratchpad: {agent_scratchpad}

    Answer in a brief sentence with the most relevant information.
    """
)
