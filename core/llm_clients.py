import os
import json
import time
import logging
from typing import Type, TypeVar, Optional, Any, List
from pydantic import BaseModel
from google import genai
from google.genai import types
import groq
from core.schemas import LLMMetrics

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMException(Exception):
    pass

class LLMProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str, response_model: Optional[Type[T]] = None) -> tuple[str, int]:
        """Returns a tuple of (response_text, latency_ms)"""
        raise NotImplementedError

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name)
        self.client = genai.Client()

    def generate(self, system_prompt: str, user_prompt: str, response_model: Optional[Type[T]] = None) -> tuple[str, int]:
        start_time = time.time()
        config_args = {"system_instruction": system_prompt, "temperature": 0.2}
        if response_model:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = response_model
        
        config = types.GenerateContentConfig(**config_args)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config,
            )
            latency = int((time.time() - start_time) * 1000)
            return response.text, latency
        except Exception as e:
            raise LLMException(f"Gemini error: {str(e)}")

class GroqProvider(LLMProvider):
    def __init__(self, model_name: str = "llama3-70b-8192"):
        super().__init__(model_name)
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing")
        self.client = groq.Groq(api_key=api_key)

    def generate(self, system_prompt: str, user_prompt: str, response_model: Optional[Type[T]] = None) -> tuple[str, int]:
        start_time = time.time()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
        }
        
        if response_model:
            kwargs["response_format"] = {"type": "json_object"}
            
        try:
            response = self.client.chat.completions.create(**kwargs)
            latency = int((time.time() - start_time) * 1000)
            return response.choices[0].message.content, latency
        except Exception as e:
            raise LLMException(f"Groq error: {str(e)}")

class OpenRouterProvider(LLMProvider):
    def __init__(self, model_name: str = "anthropic/claude-3-haiku"):
        super().__init__(model_name)
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing")
        self.api_key = api_key
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, system_prompt: str, user_prompt: str, response_model: Optional[Type[T]] = None) -> tuple[str, int]:
        import requests
        start_time = time.time()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
        }
        
        if response_model:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            latency = int((time.time() - start_time) * 1000)
            return text, latency
        except Exception as e:
            raise LLMException(f"OpenRouter error: {str(e)}")

class LLMManager:
    def __init__(self):
        self.providers = {}
        # Try to initialize providers
        try:
            self.providers["gemini_flash"] = GeminiProvider("gemini-2.5-flash")
            self.providers["gemini_pro"] = GeminiProvider("gemini-2.5-pro")
        except Exception as e:
            logger.warning(f"Failed to init Gemini: {e}")
            
        try:
            self.providers["groq"] = GroqProvider()
        except Exception as e:
            logger.warning(f"Failed to init Groq: {e}")
            
        try:
            self.providers["openrouter"] = OpenRouterProvider()
        except Exception as e:
            logger.warning(f"Failed to init OpenRouter: {e}")

    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        primary_provider: str = "gemini_flash",
        fallback_providers: List[str] = ["groq", "openrouter"],
        response_model: Optional[Type[T]] = None,
        max_retries: int = 2
    ) -> tuple[Any, LLMMetrics]:
        
        providers_to_try = [primary_provider] + fallback_providers
        
        for p_idx, provider_name in enumerate(providers_to_try):
            if provider_name not in self.providers:
                logger.warning(f"Provider {provider_name} not available, skipping.")
                continue
                
            provider = self.providers[provider_name]
            is_fallback = p_idx > 0
            
            for retry in range(max_retries + 1):
                try:
                    text, latency = provider.generate(system_prompt, user_prompt, response_model)
                    
                    if response_model:
                        try:
                            parsed_obj = response_model.model_validate_json(text)
                            metrics = LLMMetrics(
                                provider_used=provider_name,
                                fallback_triggered=is_fallback,
                                latency_ms=latency,
                                retry_count=retry,
                                structured_parse_success=True
                            )
                            return parsed_obj, metrics
                        except Exception as parse_error:
                            logger.warning(f"Failed to parse JSON from {provider_name}: {parse_error}. Text: {text}")
                            if retry == max_retries:
                                raise LLMException(f"Parse error after {max_retries} retries")
                            continue # Try again
                    else:
                        metrics = LLMMetrics(
                            provider_used=provider_name,
                            fallback_triggered=is_fallback,
                            latency_ms=latency,
                            retry_count=retry,
                            structured_parse_success=True
                        )
                        return text, metrics
                        
                except Exception as e:
                    logger.error(f"Error calling {provider_name} (retry {retry}/{max_retries}): {e}")
                    if retry == max_retries:
                        break # Try next provider
                        
        # If we get here, all providers failed
        metrics = LLMMetrics(
            provider_used="none",
            fallback_triggered=True,
            latency_ms=0,
            retry_count=max_retries,
            structured_parse_success=False,
            error_message="All providers failed"
        )
        return None, metrics
