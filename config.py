"""Configuration management for PR Auto Reviewer."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # GitHub
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

    # Claude
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # Vertex AI (for Gemini)
    VERTEX_AI_PROJECT_ID = os.getenv('VERTEX_AI_PROJECT_ID')
    VERTEX_AI_LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')

    # Model Selection
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'claude-code')

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is required")

        if cls.DEFAULT_MODEL == 'claude' and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude model")

        if cls.DEFAULT_MODEL == 'claude-code':
            # Claude Code uses its own authentication
            # Just check that it's available (will be checked in ClaudeCodeModel)
            pass

        if cls.DEFAULT_MODEL == 'gemini':
            if not cls.VERTEX_AI_PROJECT_ID:
                raise ValueError("VERTEX_AI_PROJECT_ID is required for Gemini model")

        return True
