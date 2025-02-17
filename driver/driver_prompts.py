import random
from enum import Enum
from models.driver_models import Trip, DriverProfile

driver_context = 'You are an experienced truck driver writing a complaint.'

class ComplaintTopic(Enum):
    OPERATIONS = "Operations"
    FINANCE = "Finance"
    HR = "Human Resources"

class PromptGenerator:
    """Generates complaint messages using OpenAI based on trip data and driver profile"""
    def __init__(self):
        self._topic_weights = {
            ComplaintTopic.OPERATIONS: 0.5,
            ComplaintTopic.FINANCE: 0.3,
            ComplaintTopic.HR: 0.2
        }

    def _select_topic(self) -> ComplaintTopic:
        """Randomly select a topic based on predefined weights"""
        topics, weights = zip(*self._topic_weights.items())
        return random.choices(topics, weights=weights)[0]

    def generate_prompt(self, trip: Trip, driver: DriverProfile) -> str:
        """Generate the prompt for OpenAI based on trip and driver data"""
        topic = self._select_topic()
        return f"""Assume you are a trailer driver with the following profile:
- Age: {driver.age}
- Years of experience: {driver.years_experience}

You just completed route {trip.route_id} and need to file a complaint about the {topic.value} department.
Write a detailed complaint message describing issues you encountered. The trip took {(trip.completion_datetime - trip.start_datetime).total_seconds() / 3600} hours.

Additional context:
- Was the delivery on time? {"Yes" if trip.on_time else "No"}
- Did you experience any assault? {"Yes" if trip.assaulted else "No"}
- Stress level during trip: {trip.stress_score*10}/10
- Overall trouble score: {trip.trouble_score*10}/10

Write a one paragraph complaint in first person perspective, be specific about the issues in a short paragraph. Informal language is acceptable. Just write the body of the complain message."""
