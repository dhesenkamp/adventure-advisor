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
    """Look up the weather if a date and location are provided by the user in his or her query. Transform any date mentioned by the user into a date format YYYY-MM-DD.

    User input: {input}

    Your scratchpad: {agent_scratchpad}

    Answer in a brief sentence with the most relevant information. Do not include unnecessary details or information, if the user has not asked for it. Do not include anything that is not related to the weather.
    """
)
