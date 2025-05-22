import json
import ast
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage

from agents.base_agent import BaseAgent
from agents.orchestrator.prompt_template import ROUTER_PROMPT, SUMMARY_PROMPT


@dataclass
class AgentResponse:
  agent_name: str
  success: bool
  data: Any
  raw_output: str
  error: Optional[str] = None


@dataclass
class ConversationContext:
  userPreferences: Dict[str, Any]
  gatheredInfo: Dict[str, Any]
  pendingClarifications: List[str]
  lastActivitySuggestions: List[Dict[str, Any]]


class ImprovedOrchestratorAgent(BaseAgent):

  def __init__(self, apiKey: str, agents: Dict[str, Any]):
    super().__init__(apiKey=apiKey)
    self.agents = agents

    # Add conversation memory
    self.memory = ConversationBufferWindowMemory(
        k=10,  # Keep last 10 exchanges
        return_messages=True,
        memory_key="chat_history"
    )

    # Conversation context
    self.context = ConversationContext(
        userPreferences={},
        gatheredInfo={},
        pendingClarifications=[],
        lastActivitySuggestions=[]
    )

    # Enhanced prompts
    self.router_prompt = self._build_enhanced_router_prompt()
    self.reasoning_prompt = self._build_reasoning_prompt()
    self.summary_prompt = self._build_enhanced_summary_prompt()

  def _build_enhanced_router_prompt(self) -> ChatPromptTemplate:
    """Build enhanced router prompt with better decision making"""
    template = """
You are an intelligent router for an Adventure Advisor system. Your goal is to help users find suitable outdoor activities.

CONVERSATION HISTORY:
{chat_history}

CURRENT CONTEXT:
- User preferences: {userPreferences}
- Previously gathered info: {gatheredInfo}
- Pending clarifications: {pendingClarifications}

CURRENT USER INPUT: {input}

AVAILABLE AGENTS:
- calendar: Check user's schedule, availability for specific dates
- weather: Get weather forecasts for locations and dates  
- database: Query outdoor activities database (hiking, biking, etc.)

ROUTING LOGIC:
1. If user mentions dates/times → include "calendar"
2. If user mentions weather concerns or outdoor activities → include "weather" 
3. If user asks for activity recommendations → always include "database"
4. If you have incomplete info for good recommendations → ask clarifying questions

ANALYSIS:
1. What information do we still need?
2. Which agents can provide that information?
3. Can we make good recommendations with current info?

Return your decision as a JSON object:
{{
    "agents_to_call": ["agent1", "agent2"],
    "reasoning": "Why you chose these agents",
    "clarifying_questions": ["question1", "question2"],
    "sufficient_info": true/false
}}
"""
    return ChatPromptTemplate.from_template(template)

  def _build_reasoning_prompt(self) -> ChatPromptTemplate:
    """Build prompt for reasoning over agent responses"""
    template = """
You are analyzing agent responses to provide intelligent recommendations.

USER QUERY: {user_query}
CONVERSATION CONTEXT: {context}

AGENT RESPONSES:
{agent_responses}

REASONING TASKS:
1. Extract key information from each agent response
2. Identify conflicts or missing information
3. Synthesize information to understand user's situation
4. Determine if we have enough info for good recommendations

Provide your analysis as JSON:
{{
    "key_info": {{
        "calendar": "summary of calendar info",
        "weather": "summary of weather info", 
        "database": "summary of activity matches"
    }},
    "user_situation": "综合分析用户情况",
    "missing_info": ["what info is still needed"],
    "recommendations_ready": true/false,
    "reasoning": "your step-by-step analysis"
}}
"""
    return ChatPromptTemplate.from_template(template)

  def _build_enhanced_summary_prompt(self) -> ChatPromptTemplate:
    """Build enhanced summary prompt for final response"""
    template = """
You are a helpful Adventure Advisor assistant. Create a natural, conversational response.

USER QUERY: {user_query}
CONVERSATION HISTORY: {chat_history}
ANALYSIS: {analysis}
AGENT DATA: {agent_data}

RESPONSE GUIDELINES:
1. Be conversational and helpful
2. If recommending activities, explain why they're good fits
3. Include relevant weather/calendar considerations  
4. If info is missing, ask specific follow-up questions
5. Acknowledge previous conversation context

Create a natural response that helps the user plan their outdoor adventure.
"""
    return ChatPromptTemplate.from_template(template)

  def enhanced_routing(self, query: str) -> Dict[str, Any]:
    """Enhanced routing with better decision making"""
    try:
      # Get chat history
      chat_history = self.memory.chat_memory.messages[-6:
                                                      ] if self.memory.chat_memory.messages else []

      prompt = self.router_prompt.format_messages(
          input=query,
          chat_history=chat_history,
          userPreferences=self.context.userPreferences,
          gatheredInfo=self.context.gatheredInfo,
          pendingClarifications=self.context.pendingClarifications
      )

      response = self.model.invoke(prompt)

      # Try to parse JSON response
      try:
        routing_decision = json.loads(response.content)
        return routing_decision
      except json.JSONDecodeError:
        # Fallback to simple parsing
        return {
            "agents_to_call": self._extract_agents_fallback(response.content),
            "reasoning": "Fallback parsing used",
            "clarifying_questions": [],
            "sufficient_info": False
        }

    except Exception as e:
      return {
          "agents_to_call": ["database"],  # Safe fallback
          "reasoning": f"Error in routing: {str(e)}",
          "clarifying_questions": [],
          "sufficient_info": False
      }

  def _extract_agents_fallback(self, content: str) -> List[str]:
    """Fallback method to extract agents from response"""
    agents = []
    content_lower = content.lower()

    if "calendar" in content_lower:
      agents.append("calendar")
    if "weather" in content_lower:
      agents.append("weather")
    if "database" in content_lower or "activities" in content_lower:
      agents.append("database")

    return agents if agents else ["database"]

  def call_agents(self, query: str, selected_agents: List[str]) -> List[AgentResponse]:
    """Call selected agents and structure their responses"""
    responses = []

    for agent_name in selected_agents:
      if agent_name not in self.agents:
        continue

      try:
        result = self.agents[agent_name].run(query)

        # Extract structured data if possible
        structured_data = self._extract_structured_data(
            result.get("output", ""))

        responses.append(AgentResponse(
            agent_name=agent_name,
            success=True,
            data=structured_data,
            raw_output=result.get("output", ""),
            error=None
        ))

      except Exception as e:
        responses.append(AgentResponse(
            agent_name=agent_name,
            success=False,
            data=None,
            raw_output="",
            error=str(e)
        ))

    return responses

  def _extract_structured_data(self, output: str) -> Any:
    """Extract JSON data from agent output if present"""
    try:
      # Look for JSON in the output
      start_idx = output.find('{')
      end_idx = output.rfind('}') + 1

      if start_idx != -1 and end_idx != -1:
        json_str = output[start_idx:end_idx]
        return json.loads(json_str)
    except:
      pass

    return {"raw_text": output}

  def reason_over_responses(self, query: str, responses: List[AgentResponse]) -> Dict[str, Any]:
    """Analyze and reason over agent responses"""
    # Format agent responses for the prompt
    agent_responses_text = ""
    for resp in responses:
      status = "SUCCESS" if resp.success else "FAILED"
      agent_responses_text += f"\n{resp.agent_name.upper()} ({status}):\n{resp.raw_output}\n"
      if resp.error:
        agent_responses_text += f"Error: {resp.error}\n"

    try:
      prompt = self.reasoning_prompt.format_messages(
          user_query=query,
          context=self.context.__dict__,
          agent_responses=agent_responses_text
      )

      response = self.model.invoke(prompt)
      return json.loads(response.content)

    except Exception as e:
      # Fallback reasoning
      return {
          "key_info": {resp.agent_name: resp.raw_output for resp in responses if resp.success},
          "user_situation": "Unable to fully analyze due to parsing error",
          "missing_info": [],
          "recommendations_ready": len([r for r in responses if r.success and r.agent_name == "database"]) > 0,
          "reasoning": f"Fallback analysis due to error: {str(e)}"
      }

  def update_context(self, query: str, responses: List[AgentResponse], analysis: Dict[str, Any]):
    """Update conversation context with new information"""
    # Update gathered info
    for resp in responses:
      if resp.success and resp.data:
        self.context.gatheredInfo[resp.agent_name] = resp.data

    # Extract user preferences from the query
    self._extract_preferences_from_query(query)

    # Update pending clarifications
    if "missing_info" in analysis:
      self.context.pendingClarifications = analysis["missing_info"]

  def _extract_preferences_from_query(self, query: str):
    """Extract user preferences from query and update context"""
    query_lower = query.lower()

    # Extract difficulty preferences
    if "easy" in query_lower or "beginner" in query_lower:
      self.context.userPreferences["difficulty"] = 0
    elif "medium" in query_lower or "moderate" in query_lower:
      self.context.userPreferences["difficulty"] = 1
    elif "hard" in query_lower or "difficult" in query_lower or "challenging" in query_lower:
      self.context.userPreferences["difficulty"] = 2

    # Extract activity type preferences
    if "hik" in query_lower:
      self.context.userPreferences["activity"] = "hiking"
    elif "bik" in query_lower or "cycl" in query_lower:
      self.context.userPreferences["activity"] = "biking"

    # Extract duration preferences
    if "hour" in query_lower:
      import re
      hours = re.findall(r'(\d+)\s*hour', query_lower)
      if hours:
        self.context.userPreferences["duration_hours"] = int(hours[0])

  def generate_final_response(self, query: str, analysis: Dict[str, Any], responses: List[AgentResponse]) -> str:
    """Generate final conversational response"""
    try:
      # Get chat history
      chat_history = self.memory.chat_memory.messages[-4:
                                                      ] if self.memory.chat_memory.messages else []

      # Format agent data
      agent_data = {}
      for resp in responses:
        if resp.success:
          agent_data[resp.agent_name] = resp.data

      prompt = self.summary_prompt.format_messages(
          user_query=query,
          chat_history=chat_history,
          analysis=json.dumps(analysis, indent=2),
          agent_data=json.dumps(agent_data, indent=2)
      )

      response = self.model.invoke(prompt)
      return response.content

    except Exception as e:
      # Fallback response
      return self._generate_fallback_response(query, responses, analysis)

  def _generate_fallback_response(self, query: str, responses: List[AgentResponse], analysis: Dict[str, Any]) -> str:
    """Generate a basic fallback response"""
    response_parts = ["I'd be happy to help you plan your outdoor adventure!"]

    # Add info from successful agent calls
    for resp in responses:
      if resp.success and resp.raw_output:
        response_parts.append(f"\n{resp.raw_output}")

    if analysis.get("missing_info"):
      response_parts.append(
          f"\nTo give you better recommendations, could you tell me more about: {', '.join(analysis['missing_info'])}")

    return "\n".join(response_parts)

  def run(self, query: str) -> str:
    """Enhanced run method with full conversation flow"""
    try:
      # 1. Enhanced routing
      routing_decision = self.enhanced_routing(query)

      # 2. Handle clarifying questions
      if routing_decision.get("clarifying_questions") and not routing_decision.get("sufficient_info"):
        clarifying_response = "I'd love to help you find the perfect outdoor activity! " + \
            " ".join(routing_decision["clarifying_questions"])

        # Save to memory
        self.memory.chat_memory.add_user_message(query)
        self.memory.chat_memory.add_ai_message(clarifying_response)

        return clarifying_response

      # 3. Call selected agents
      selected_agents = routing_decision.get("agents_to_call", ["database"])
      agent_responses = self.call_agents(query, selected_agents)

      # 4. Reason over responses
      analysis = self.reason_over_responses(query, agent_responses)

      # 5. Update context
      self.update_context(query, agent_responses, analysis)

      # 6. Generate final response
      final_response = self.generate_final_response(
          query, analysis, agent_responses)

      # 7. Save to memory
      self.memory.chat_memory.add_user_message(query)
      self.memory.chat_memory.add_ai_message(final_response)

      return final_response

    except Exception as e:
      error_response = f"I apologize, but I encountered an error while processing your request. Let me try to help you anyway. Could you tell me what kind of outdoor activity you're interested in?"

      # Still save to memory
      self.memory.chat_memory.add_user_message(query)
      self.memory.chat_memory.add_ai_message(error_response)

      return error_response

  def get_conversation_summary(self) -> Dict[str, Any]:
    """Get summary of current conversation state"""
    return {
        "context": self.context.__dict__,
        "message_count": len(self.memory.chat_memory.messages),
        "last_messages": [msg.content for msg in self.memory.chat_memory.messages[-4:]]
    }
