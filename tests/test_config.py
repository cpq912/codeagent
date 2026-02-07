import os
import pytest
from pydantic import ValidationError
from codeagent.config import Settings

def test_load_config_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.test.com")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    
    settings = Settings()
    
    assert settings.openai_api_key == "test_key"
    assert settings.openai_base_url == "https://api.test.com"
    assert settings.openai_model == "test-model"

def test_missing_api_key(monkeypatch):
    """Test that validation fails when API Key is missing."""
    # Clear environment variables
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Ensure .env file doesn't interfere (SettingsConfigDict handles this, 
    # but for unit tests we want to be sure environment is clean)
    # Note: Settings priority is Env Vars > .env file > defaults
    
    # We expect ValidationError because openai_api_key is required (Field(...))
    # However, if .env exists in CWD, it might load it. 
    # For robust testing, we should probably mock the .env file loading or run in a clean CWD.
    # Here we assume no .env exists or we override it.
    
    # Mocking SettingsConfigDict to ignore .env file for this test is hard on instance.
    # Instead we rely on the fact that we haven't created .env yet in the test environment,
    # or we can override env_file to a non-existent one.
    
    with pytest.raises(ValidationError):
        Settings(_env_file='non_existent_file')
