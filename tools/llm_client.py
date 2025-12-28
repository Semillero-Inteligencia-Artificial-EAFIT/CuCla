import anthropic
import openai
from openai import OpenAI
#import google.generativeai as genai


class LLMChat:

    @staticmethod
    def chatgpt(prompt: str, api_key: str, model: str = "gpt-4") -> str:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    @staticmethod
    def claude(prompt: str, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    @staticmethod
    def gemini(prompt: str, api_key: str, model: str = "gemini-pro") -> str:
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(prompt)
        return response.text

    @staticmethod
    def llmstudio(prompt: str, base_url: str, api_key: str = "not-needed", model: str = "local-model") -> str:
        # LLM Studio uses OpenAI-compatible API
        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
