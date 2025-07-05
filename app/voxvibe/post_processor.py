import logging
import os
from typing import Optional

import litellm

logger = logging.getLogger(__name__)


class PostProcessor:
    """Post-processes transcribed text using LLM to improve formatting and fix transcription issues."""
    
    def __init__(self, model: str = "openai/gpt-4.1-mini", temperature: float = 0.3, setenv: Optional[dict] = None):
        """
        Initialize the post-processor.
        
        Args:
            model: LLM model to use for post-processing (with provider prefix)
            temperature: Temperature setting for the LLM
            setenv: Dictionary of environment variables to set for LLM providers
        """
        self.model = model
        self.temperature = temperature
        self._system_prompt = self._create_system_prompt()
        
        # Set environment variables if provided
        if setenv:
            for key, value in setenv.items():
                os.environ[key] = value
                logger.info(f"Environment variable {key} configured")
        
        # Configure litellm settings
        litellm.set_verbose = False  # Reduce noise in logs
        
        # Configure LiteLLM logging to match VoxVibe format or suppress it
        litellm_logger = logging.getLogger("LiteLLM")
        litellm_logger.setLevel(logging.WARNING)  # Only show warnings and errors
        
        # Also suppress the httpx logs that LiteLLM uses
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.setLevel(logging.WARNING)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for post-processing."""
        return """You are a text post-processor that improves transcribed voice recordings. Your task is to:

1. Fix transcription errors and typos
2. Improve formatting and readability
3. Use proper punctuation and capitalization
4. Convert lists into bullet points when appropriate
5. Fix common speech-to-text errors (homophones, word boundaries, etc.)
6. Maintain the original meaning and tone
7. Keep the text concise and clear

Guidelines:
- If the text contains a list of items, format it with bullet points
- Fix obvious transcription errors (e.g., "their" vs "there", "to" vs "too")
- Add appropriate punctuation and capitalization
- Break long sentences into shorter, clearer ones when needed
- Preserve the speaker's intent and meaning
- Don't add new information or change the core message

Return only the improved text, no explanations or commentary."""

    def process(self, text: str) -> Optional[str]:
        """
        Post-process the transcribed text using LLM.
        
        Args:
            text: Raw transcribed text to process
            
        Returns:
            Improved text or None if processing failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for post-processing")
            return None
        
        try:
            logger.debug(f"Post-processing text: {text[:100]}...")
            
            # Create the user prompt
            user_prompt = f"Please improve this transcribed text:\n\n{text}"
            
            # Call the LLM
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000,
                timeout=30
            )
            
            # Extract the improved text
            improved_text = response.choices[0].message.content.strip()
            
            if improved_text:
                logger.debug(f"Post-processing completed: {improved_text[:100]}...")
                return improved_text
            else:
                logger.warning("LLM returned empty response")
                return text  # Return original text if LLM fails
                
        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            return text  # Return original text if processing fails
    
    def set_model(self, model: str):
        """Change the LLM model used for post-processing."""
        self.model = model
        logger.info(f"Post-processor model changed to: {model}")
    
    def set_temperature(self, temperature: float):
        """Change the temperature setting for the LLM."""
        self.temperature = temperature
        logger.info(f"Post-processor temperature changed to: {temperature}")