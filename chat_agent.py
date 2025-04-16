# chat_agent.py

# Standard library imports
import time

# Related third party imports
import requests
import json


# Local application/library specific imports
# (Add your local module imports if needed)


# Constants
API_KEY = <API_KEY>  # Replace with your DeepSeek API key

class ChatAgent:
  """
  ChatAgent represents an intelligent chat-based agent that uses the DeepSeek API.
  The agent utilizes the OpenAI SDK configured to use DeepSeek's endpoint.
  """

  def __init__(self, agentName):
    """
    Initializes the agent with the given name.
    """
    self.agentName = agentName
    self.messageHistory = []  # List to store conversation history
  

  def callLLM(self, prompt):
    """
    Calls the DeepSeek API using the OpenAI SDK with the given prompt and returns the response.
    
    Args:
      prompt (str): The prompt or message from the user.
      
    Returns:
      str: The response from DeepSeek.
    """
    # Prepare the conversation structure with the system message and user prompt
    messages = [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": prompt}
    ]

    try:
      response = requests.post(
        url = "https://openrouter.ai/api/v1/chat/completions",
        headers = {"Authorization": API_KEY},
        data = json.dumps({
          "model": "gemini-2.0-flash-exp",
          "messages": messages

        })
      )

      # According to documentation, the response should include a list of choices
      response_json = response.json()
      # Debug: print the full JSON response to understand its structure.
      print("DEBUG: Full response JSON:")
      print(json.dumps(response_json, indent=2))

      agentReply = response.choices[0].message.content.strip()
      return agentReply
    except Exception as e:
      return f"Error calling Gemini LLM: {str(e)}"

  def interactWithUser(self):
    """
    Interacts with the user via the console.
    It reads user input, sends it to the DeepSeek API via callLLM,
    prints the response, and updates the conversation history.
    """
    print(f"Hi, I am {self.agentName}. How can I help you today?")
    while True:
      userInput = input("You: ").strip()
      if userInput.lower() in ["exit", "quit"]:
        print("Chat ended.")
        break

      # Save the user input in history
      self.messageHistory.append({"user": userInput})

      # Call the DeepSeek API to get a response
      llmResponse = self.callLLM(userInput)

      # Save the DeepSeek response in history
      self.messageHistory.append({"llm": llmResponse})

      print(f"{self.agentName}: {llmResponse}")
      time.sleep(0.5)

  def sendMessageToAgent(self, targetAgentUrl, message):
    """
    Sends a message to another agent following the Agent2Agent protocol.
    This stub should be extended based on your system's specifics.
    
    Args:
      targetAgentUrl (str): The URL where the target agent listens.
      message (str): The message to be sent.
      
    Returns:
      dict: The response from the target agent.
    """
    # In a real implementation, consider using requests or another HTTP client
    # to send the message following the protocol.
    payload = {
      "sender": self.agentName,
      "message": message,
      "timestamp": time.time()
    }

    # Stub implementation: simply print the payload.
    print(f"Sending message to {targetAgentUrl} with payload: {payload}")
    return {"status": "sent", "payload": payload}

  def receiveMessageFromAgent(self, messagePayload):
    """
    Processes a message received from another agent following the Agent2Agent protocol.
    
    Args:
      messagePayload (dict): A dictionary containing keys such as 'sender', 'message', and 'timestamp'.
      
    Returns:
      str: An acknowledgment message.
    """
    sender = messagePayload.get("sender", "Unknown")
    message = messagePayload.get("message", "")
    timestamp = messagePayload.get("timestamp", time.time())

    # Log the incoming message
    self.messageHistory.append({"agent": sender, "message": message, "timestamp": timestamp})
    print(f"Received message from {sender}: {message}")

    ackMessage = f"Acknowledged message from {sender}."
    return ackMessage

if __name__ == "__main__":
  #configure()
  agent = ChatAgent("DeepSeekChatAgent")
  agent.interactWithUser()
