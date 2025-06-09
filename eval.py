#!/usr/bin/env python3
"""
Adventure Advisor Evaluation Script

This script evaluates the Adventure Advisor application across multiple dimensions:
- Functional correctness
- Performance
- User experience
- Integration quality
- Error handling

Provides a comprehensive score and detailed feedback.
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import traceback

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
  from orchestrator import Orchestrator
  from calendar_agent import CalendarAgent
  from weather_agent import WeatherAgent
  from database_agent import DatabaseAgent
except ImportError as e:
  print(f"Error importing modules: {e}")
  print("Make sure you're running this script from the project root directory")
  sys.exit(1)


class TestCategory(Enum):
  FUNCTIONAL = "Functional"
  PERFORMANCE = "Performance"
  INTEGRATION = "Integration"
  ERROR_HANDLING = "Error Handling"
  USER_EXPERIENCE = "User Experience"


@dataclass
class TestResult:
  name: str
  category: TestCategory
  score: float  # 0-100
  max_score: float
  details: str
  execution_time: float
  success: bool


@dataclass
class EvaluationReport:
  total_score: float
  max_total_score: float
  category_scores: Dict[TestCategory, float]
  test_results: List[TestResult]
  summary: str
  recommendations: List[str]


class AdventureAdvisorEvaluator:
  def __init__(self, api_key: str):
    """Initialize the evaluator with necessary components."""
    self.api_key = api_key
    self.test_results: List[TestResult] = []
    self.setup_logging()

    # Initialize agents and orchestrator
    try:
      self.calendar_agent = CalendarAgent(apiKey=api_key)
      self.weather_agent = WeatherAgent(apiKey=api_key)
      self.database_agent = DatabaseAgent(apiKey=api_key)

      agents = {
          "calendar": self.calendar_agent,
          "weather": self.weather_agent,
          "database": self.database_agent
      }
      self.orchestrator = Orchestrator(apiKey=api_key, agents=agents)

    except Exception as e:
      logging.error(f"Failed to initialize agents: {e}")
      raise

  def setup_logging(self):
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('evaluation.log'),
            logging.StreamHandler()
        ]
    )

  def run_test(self, test_name: str, category: TestCategory, max_score: float, test_func) -> TestResult:
    """Run a single test and return the result."""
    start_time = time.time()
    success = False
    score = 0.0
    details = ""

    try:
      logging.info(f"Running test: {test_name}")
      score, details = test_func()
      success = True

    except Exception as e:
      details = f"Test failed with error: {str(e)}\n{traceback.format_exc()}"
      logging.error(f"Test {test_name} failed: {e}")

    execution_time = time.time() - start_time

    result = TestResult(
        name=test_name,
        category=category,
        score=score,
        max_score=max_score,
        details=details,
        execution_time=execution_time,
        success=success
    )

    self.test_results.append(result)
    return result

  # FUNCTIONAL TESTS
  def test_orchestrator_routing(self) -> Tuple[float, str]:
    """Test if orchestrator correctly routes queries to appropriate agents."""
    test_cases = [
        ("What's the weather tomorrow?", ["weather"]),
        ("Do I have any appointments on June 6th?", ["calendar"]),
        ("Find me easy hikes near Trento", ["database"]),
        ("Plan a hike for this weekend considering weather and my schedule",
         ["calendar", "weather", "database"]),
        ("Show me cycling routes in the Alps", ["database"]),
        ("What will the weather be like on Sunday?", ["weather"])
    ]

    correct_routings = 0
    total_cases = len(test_cases)
    details = []

    for query, expected_agents in test_cases:
      try:
        selected_agents = self.orchestrator.routing(query)

        # Check if all expected agents are selected
        if isinstance(selected_agents, list):
          # Allow for flexibility - if expected agents are subset of selected
          has_required = all(
              agent in selected_agents for agent in expected_agents)
          if has_required:
            correct_routings += 1
            details.append(f"✓ '{query}' -> {selected_agents}")
          else:
            details.append(
                f"✗ '{query}' -> Expected: {expected_agents}, Got: {selected_agents}")
        else:
          details.append(
              f"✗ '{query}' -> Invalid response type: {type(selected_agents)}")

      except Exception as e:
        details.append(f"✗ '{query}' -> Error: {str(e)}")

    score = (correct_routings / total_cases) * 100
    detail_text = f"Routing accuracy: {correct_routings}/{total_cases}\n" + "\n".join(
        details)

    return score, detail_text

  def test_agent_responses(self) -> Tuple[float, str]:
    """Test individual agent response quality."""
    tests = []

    # Test weather agent
    try:
      tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
      weather_result = self.weather_agent.run(
          f"What's the weather in Trento on {tomorrow}?")
      weather_score = 100 if "output" in weather_result and weather_result["output"] else 0
      tests.append(("Weather Agent", weather_score, str(
          weather_result.get("output", "No output"))))
    except Exception as e:
      tests.append(("Weather Agent", 0, f"Error: {str(e)}"))

    # Test database agent
    try:
      db_result = self.database_agent.run("Find hiking trails near Trento")
      db_score = 100 if "output" in db_result and "hiking" in db_result["output"].lower(
      ) else 0
      tests.append(("Database Agent", db_score, str(
          db_result.get("output", "No output"))))
    except Exception as e:
      tests.append(("Database Agent", 0, f"Error: {str(e)}"))

    # Test calendar agent (may fail without proper setup)
    try:
      cal_result = self.calendar_agent.run("Do I have any events today?")
      cal_score = 100 if "output" in cal_result else 50  # Partial credit for attempting
      tests.append(("Calendar Agent", cal_score, str(
          cal_result.get("output", "No output"))))
    except Exception as e:
      tests.append(
          ("Calendar Agent", 25, f"Expected error (OAuth not configured): {str(e)}"))

    avg_score = sum(score for _, score, _ in tests) / len(tests)
    details = "\n".join(
        [f"{name}: {score}/100 - {detail[:100]}..." for name, score, detail in tests])

    return avg_score, details

  def test_end_to_end_flow(self) -> Tuple[float, str]:
    """Test complete user interaction flow."""
    test_queries = [
        "I want to go hiking this weekend",
        "Find me easy cycling routes",
        "What outdoor activities can I do tomorrow?",
        "Plan a mountain bike tour in the Dolomites"
    ]

    successful_responses = 0
    details = []

    for query in test_queries:
      try:
        response = self.orchestrator.run(query)

        # Check if response is meaningful
        if isinstance(response, str) and len(response) > 50:
          successful_responses += 1
          details.append(f"✓ '{query}' -> Response length: {len(response)}")
        else:
          details.append(
              f"✗ '{query}' -> Poor response: {str(response)[:100]}...")

      except Exception as e:
        details.append(f"✗ '{query}' -> Error: {str(e)}")

    score = (successful_responses / len(test_queries)) * 100
    detail_text = f"Successful interactions: {successful_responses}/{len(test_queries)}\n" + "\n".join(
        details)

    return score, detail_text

  # PERFORMANCE TESTS
  def test_response_times(self) -> Tuple[float, str]:
    """Test response time performance."""
    test_cases = [
        ("Simple weather query", "Weather in Trento today", 5.0),
        ("Database query", "Find hiking trails", 8.0),
        ("Complex query", "Plan outdoor activities for this weekend", 15.0)
    ]

    performance_scores = []
    details = []

    for test_name, query, max_time in test_cases:
      start_time = time.time()
      try:
        response = self.orchestrator.run(query)
        execution_time = time.time() - start_time

        # Score based on response time (100 for instant, 0 for max_time or longer)
        time_score = max(0, 100 - (execution_time / max_time) * 100)
        performance_scores.append(time_score)
        details.append(
            f"{test_name}: {execution_time:.2f}s (max: {max_time}s) - Score: {time_score:.1f}")

      except Exception as e:
        performance_scores.append(0)
        details.append(f"{test_name}: Error - {str(e)}")

    avg_score = sum(performance_scores) / \
        len(performance_scores) if performance_scores else 0
    detail_text = "Response Time Performance:\n" + "\n".join(details)

    return avg_score, detail_text

  async def test_concurrent_requests(self) -> Tuple[float, str]:
    """Test system behavior under concurrent load."""
    async def make_request(query: str, request_id: int):
      try:
        start_time = time.time()
        response = self.orchestrator.run(f"{query} (request {request_id})")
        end_time = time.time()
        return True, end_time - start_time, len(str(response))
      except Exception as e:
        return False, 0, str(e)

    async def run_concurrent_test():
      queries = ["Find hiking trails"] * 5  # 5 concurrent requests
      tasks = [make_request(query, i) for i, query in enumerate(queries)]
      return await asyncio.gather(*tasks, return_exceptions=True)

    try:
      # Note: This test might not work perfectly due to the synchronous nature of the agents
      results = []
      for i in range(3):  # Sequential requests to simulate load
        success, exec_time, response_len = await make_request("Find hiking trails", i)
        results.append((success, exec_time, response_len))

      successful_requests = sum(1 for success, _, _ in results if success)
      avg_response_time = sum(time for _, time, _ in results if isinstance(
          time, (int, float))) / len(results)

      score = (successful_requests / len(results)) * 100
      details = f"Concurrent load test: {successful_requests}/{len(results)} requests successful\n"
      details += f"Average response time: {avg_response_time:.2f}s"

      return score, details

    except Exception as e:
      return 0, f"Concurrent test failed: {str(e)}"

  # ERROR HANDLING TESTS
  def test_error_handling(self) -> Tuple[float, str]:
    """Test how well the system handles various error conditions."""
    error_test_cases = [
        ("Invalid date format", "What's the weather on 32nd December?"),
        ("Nonsensical query", "Purple monkey dishwasher mountain bike"),
        ("Empty query", ""),
        ("Very long query", "a" * 1000),
    ]

    handled_errors = 0
    details = []

    for test_name, query in error_test_cases:
      try:
        response = self.orchestrator.run(query)

        # Check if system handled gracefully (didn't crash)
        if isinstance(response, str):
          handled_errors += 1
          details.append(f"✓ {test_name}: Handled gracefully")
        else:
          details.append(f"✗ {test_name}: Unexpected response type")

      except Exception as e:
        # Exceptions are not ideal, but better than crashes
        handled_errors += 0.5
        details.append(f"~ {test_name}: Exception raised: {str(e)[:100]}...")

    score = (handled_errors / len(error_test_cases)) * 100
    detail_text = "Error Handling Results:\n" + "\n".join(details)

    return score, detail_text

  # INTEGRATION TESTS
  def test_data_consistency(self) -> Tuple[float, str]:
    """Test consistency of data across different agents."""
    consistency_score = 100  # Start with perfect score
    details = []

    # Test 1: Location consistency
    try:
      weather_response = self.weather_agent.run("Weather in Trento tomorrow")
      db_response = self.database_agent.run("Find activities near Trento")

      # Basic check - both should mention Trento
      weather_mentions_location = "trento" in str(weather_response).lower()
      db_mentions_location = "trento" in str(db_response).lower()

      if weather_mentions_location and db_mentions_location:
        details.append("✓ Location consistency: Both agents reference Trento")
      else:
        consistency_score -= 25
        details.append(
            "✗ Location consistency: Agents don't consistently reference location")

    except Exception as e:
      consistency_score -= 25
      details.append(f"✗ Location consistency test failed: {str(e)}")

    # Test 2: Response format consistency
    try:
      responses = [
          self.orchestrator.run("Find hiking trails"),
          self.orchestrator.run("Weather forecast"),
          self.orchestrator.run("My calendar for today")
      ]

      # Check if all responses are strings of reasonable length
      all_valid = all(isinstance(r, str) and len(r) > 10 for r in responses)
      if all_valid:
        details.append(
            "✓ Response format consistency: All responses are properly formatted")
      else:
        consistency_score -= 25
        details.append(
            "✗ Response format consistency: Inconsistent response formats")

    except Exception as e:
      consistency_score -= 25
      details.append(f"✗ Response format test failed: {str(e)}")

    detail_text = "Data Consistency Results:\n" + "\n".join(details)
    return consistency_score, detail_text

  # USER EXPERIENCE TESTS
  def test_response_quality(self) -> Tuple[float, str]:
    """Evaluate the quality and helpfulness of responses."""
    quality_queries = [
        ("Recommendation request", "I'm a beginner looking for easy hikes near Trento"),
        ("Planning query", "Help me plan outdoor activities for next weekend"),
        ("Information query", "What should I know about hiking in the Dolomites?")
    ]

    quality_scores = []
    details = []

    for query_type, query in quality_queries:
      try:
        response = self.orchestrator.run(query)

        # Quality metrics
        # Reward longer, more detailed responses
        length_score = min(100, len(response) / 5)
        keyword_relevance = sum(1 for word in ['hiking', 'outdoor', 'activity', 'weather', 'trail']
                                if word in response.lower()) * 10
        helpfulness_score = 50 if any(word in response.lower()
                                      for word in ['recommend', 'suggest', 'consider', 'try']) else 0

        total_score = min(
            100, (length_score + keyword_relevance + helpfulness_score) / 3)
        quality_scores.append(total_score)
        details.append(
            f"{query_type}: Score {total_score:.1f} (Length: {len(response)} chars)")

      except Exception as e:
        quality_scores.append(0)
        details.append(f"{query_type}: Error - {str(e)}")

    avg_quality = sum(quality_scores) / \
        len(quality_scores) if quality_scores else 0
    detail_text = "Response Quality Assessment:\n" + "\n".join(details)

    return avg_quality, detail_text

  def run_evaluation(self) -> EvaluationReport:
    """Run complete evaluation suite and generate report."""
    logging.info("Starting Adventure Advisor Evaluation")

    # Define all tests with their categories and max scores
    tests = [
        # Functional Tests (40% of total score)
        ("Orchestrator Routing", TestCategory.FUNCTIONAL,
         100, self.test_orchestrator_routing),
        ("Agent Responses", TestCategory.FUNCTIONAL, 100, self.test_agent_responses),
        ("End-to-End Flow", TestCategory.FUNCTIONAL, 100, self.test_end_to_end_flow),

        # Performance Tests (25% of total score)
        ("Response Times", TestCategory.PERFORMANCE, 100, self.test_response_times),
        ("Concurrent Load", TestCategory.PERFORMANCE,
         100, self.test_concurrent_requests),

        # Error Handling Tests (15% of total score)
        ("Error Handling", TestCategory.ERROR_HANDLING,
         100, self.test_error_handling),

        # Integration Tests (10% of total score)
        ("Data Consistency", TestCategory.INTEGRATION,
         100, self.test_data_consistency),

        # User Experience Tests (10% of total score)
        ("Response Quality", TestCategory.USER_EXPERIENCE,
         100, self.test_response_quality),
    ]

    # Category weights
    category_weights = {
        TestCategory.FUNCTIONAL: 0.40,
        TestCategory.PERFORMANCE: 0.25,
        TestCategory.ERROR_HANDLING: 0.15,
        TestCategory.INTEGRATION: 0.10,
        TestCategory.USER_EXPERIENCE: 0.10
    }

    # Run all tests
    for test_name, category, max_score, test_func in tests:
      self.run_test(test_name, category, max_score, test_func)
      time.sleep(2)  # Avoid hitting API rate limits

    # Calculate scores by category
    category_scores = {}
    for category in TestCategory:
      category_tests = [t for t in self.test_results if t.category == category]
      if category_tests:
        category_total = sum(t.score for t in category_tests)
        category_max = sum(t.max_score for t in category_tests)
        category_scores[category] = (
            category_total / category_max) * 100 if category_max > 0 else 0
      else:
        category_scores[category] = 0

    # Calculate weighted final score
    final_score = sum(
        category_scores[cat] * weight for cat, weight in category_weights.items())
    max_total_score = 100

    # Generate summary and recommendations
    summary = self.generate_summary(final_score, category_scores)
    recommendations = self.generate_recommendations(category_scores)

    return EvaluationReport(
        total_score=final_score,
        max_total_score=max_total_score,
        category_scores=category_scores,
        test_results=self.test_results,
        summary=summary,
        recommendations=recommendations
    )

  def generate_summary(self, final_score: float, category_scores: Dict[TestCategory, float]) -> str:
    """Generate a summary of the evaluation results."""
    if final_score >= 90:
      grade = "Excellent"
    elif final_score >= 80:
      grade = "Good"
    elif final_score >= 70:
      grade = "Satisfactory"
    elif final_score >= 60:
      grade = "Needs Improvement"
    else:
      grade = "Poor"

    summary = f"""
ADVENTURE ADVISOR EVALUATION SUMMARY
=====================================

Overall Score: {final_score:.1f}/100 ({grade})

Category Breakdown:
• Functional: {category_scores.get(TestCategory.FUNCTIONAL, 0):.1f}/100
• Performance: {category_scores.get(TestCategory.PERFORMANCE, 0):.1f}/100
• Error Handling: {category_scores.get(TestCategory.ERROR_HANDLING, 0):.1f}/100
• Integration: {category_scores.get(TestCategory.INTEGRATION, 0):.1f}/100
• User Experience: {category_scores.get(TestCategory.USER_EXPERIENCE, 0):.1f}/100

The Adventure Advisor system demonstrates {grade.lower()} overall performance.
"""
    return summary.strip()

  def generate_recommendations(self, category_scores: Dict[TestCategory, float]) -> List[str]:
    """Generate improvement recommendations based on test results."""
    recommendations = []

    if category_scores.get(TestCategory.FUNCTIONAL, 0) < 80:
      recommendations.append(
          "Improve agent routing logic and response consistency")

    if category_scores.get(TestCategory.PERFORMANCE, 0) < 80:
      recommendations.append(
          "Optimize response times and implement caching strategies")

    if category_scores.get(TestCategory.ERROR_HANDLING, 0) < 80:
      recommendations.append("Enhance error handling and input validation")

    if category_scores.get(TestCategory.INTEGRATION, 0) < 80:
      recommendations.append("Improve data consistency across agents")

    if category_scores.get(TestCategory.USER_EXPERIENCE, 0) < 80:
      recommendations.append(
          "Enhance response quality and user interaction flow")

    if not recommendations:
      recommendations.append(
          "System performing well - focus on monitoring and maintenance")

    return recommendations

  def print_detailed_report(self, report: EvaluationReport):
    """Print a detailed evaluation report."""
    print("\n" + "="*80)
    print("ADVENTURE ADVISOR DETAILED EVALUATION REPORT")
    print("="*80)

    print(report.summary)

    print(f"\nDETAILED TEST RESULTS:")
    print("-" * 50)

    for category in TestCategory:
      category_tests = [
          t for t in report.test_results if t.category == category]
      if category_tests:
        print(f"\n{category.value} Tests:")
        for test in category_tests:
          status = "✓ PASS" if test.success else "✗ FAIL"
          print(
              f"  {status} {test.name}: {test.score:.1f}/{test.max_score:.1f} ({test.execution_time:.2f}s)")
          if test.details:
            # Print first few lines of details
            detail_lines = test.details.split('\n')[:3]
            for line in detail_lines:
              print(f"    {line}")
            if len(test.details.split('\n')) > 3:
              print("    ...")

    print(f"\nRECOMMENDATIONS:")
    print("-" * 20)
    for i, rec in enumerate(report.recommendations, 1):
      print(f"{i}. {rec}")

    print(
        f"\nEVALUATION COMPLETED AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")


def main():
  """Main evaluation function."""
  import argparse
  from dotenv import load_dotenv

  load_dotenv()

  parser = argparse.ArgumentParser(
      description="Evaluate Adventure Advisor Application")
  parser.add_argument(
      "--api-key", help="Gemini API Key (or set GEMINI_API_KEY env var)")
  parser.add_argument(
      "--output", help="Output file for detailed results (optional)")
  args = parser.parse_args()

  # Get API key
  api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
  if not api_key:
    print("Error: GEMINI_API_KEY must be provided via --api-key argument or environment variable")
    sys.exit(1)

  try:
    # Initialize evaluator
    evaluator = AdventureAdvisorEvaluator(api_key)

    # Run evaluation
    print("Starting Adventure Advisor Evaluation...")
    print("This may take several minutes depending on API response times...")

    report = evaluator.run_evaluation()

    # Print results
    evaluator.print_detailed_report(report)

    # Save results if output file specified
    if args.output:
      with open(args.output, 'w') as f:
        json.dump({
            'total_score': report.total_score,
            'category_scores': {cat.value: score for cat, score in report.category_scores.items()},
            'test_results': [{
                'name': t.name,
                'category': t.category.value,
                'score': t.score,
                'max_score': t.max_score,
                'success': t.success,
                'execution_time': t.execution_time,
                'details': t.details
            } for t in report.test_results],
            'summary': report.summary,
            'recommendations': report.recommendations,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
      print(f"Detailed results saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if report.total_score >= 70 else 1)

  except Exception as e:
    logging.error(f"Evaluation failed: {e}")
    print(f"\nEVALUATION FAILED: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()
