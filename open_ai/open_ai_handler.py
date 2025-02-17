import ast
from typing import Type
from openai import OpenAI, RateLimitError
from models.openai_config import OpenAIConfig, T
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


class OpenAIHandler:
    def __init__(self):
        config = OpenAIConfig
        self.api_key = config.api_key
        self.organization = config.organization
        self.project = config.project
        self.model = config.model
        self.temperature = float(config.temperature)
        self.max_tokens = int(config.max_tokens)

        # Initialize token counts
        self.tokens_unit=1000000
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.input_token_cost=0.15
        self.output_token_cost = 0.3
        self.total_prompts = 0

        self.client = self._create_client()


    def _create_client(self):
        """Sets up the OpenAI API key and base URL globally."""
        return OpenAI(
            api_key=self.api_key,
            organization=self.organization,
            project=self.project
        )

    @retry(stop=stop_after_attempt(10), wait=wait_fixed(360), retry=retry_if_exception_type(RateLimitError))
    def chat_complete_with_model(self,
                                 system_role: str,
                                 system_content: str,
                                 prompt: str,
                                 stop=None) -> str:
        """
        Method to run a chat completion and return the result as a Pydantic model.
        :param system_role: Role description of the AI assistant.
        :param prompt: The prompt string to send to the API.
        :param model_class: The Pydantic model class to deserialize the response into.
        :param max_tokens: Maximum number of tokens for the response.
        :param stop: Sequence where the API will stop generating further tokens.
        :return: The deserialized response as an instance of the provided Pydantic model class.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": system_role, "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=stop
            )

            # Extract and return the content and the token usage info

            raw_content = response.choices[0].message.content
            input_tokens, output_tokens = self._count_tokens(response)

            # Update the general token count
            self._update_total_tokens(input_tokens, output_tokens)
            self.total_prompts+=1
            return raw_content
        except Exception as e:
            print(f"Error while running text completion: {e}")
            raise RateLimitError

    @staticmethod
    def _count_tokens(response):
        """
        Method to count the input and output tokens from the response.

        :param response: The API response object.
        :return: Tuple containing the number of input and output tokens.
        """

        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        return input_tokens, output_tokens

    def _update_total_tokens(self, input_tokens, output_tokens):
        """
        Update the total input and output tokens of the class.

        :param input_tokens: The number of input tokens for this request.
        :param output_tokens: The number of output tokens for this request.
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def set_api_key(self, api_key):
        """Set a new API key if needed."""
        self.api_key = api_key
        self._create_client()

    def set_model(self, model):
        """Set a new model to be used in OpenAI API requests."""
        self.model = model

    def set_temperature(self, temperature):
        """Set a new temperature to be used in OpenAI API requests."""
        self.temperature = temperature

    def handler_cost(self):
        """
        Calculate the total cost based on token usage.
        :return: Total cost of all the tokens used.
        """
        unit = self.tokens_unit
        input_cost = (self.total_input_tokens / unit) * self.input_token_cost
        output_cost = (self.total_output_tokens / unit) * self.output_token_cost
        return input_cost + output_cost


    def handler_information(self):
        print(f'Total prompts used: {self.total_prompts}')
        print(f'Total input tokens: {self.total_input_tokens} at a cost of {str(self.input_token_cost)} per {str(self.tokens_unit)} tokens')
        print(f'Total output tokens: {self.total_output_tokens} at a cost of {str(self.output_token_cost)} per {str(self.tokens_unit)} tokens')
        print(f'Total cost of evaluation{self.handler_cost()}')
