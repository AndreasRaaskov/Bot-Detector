# config.py - Configuration management for the Bot Detector application
# This file handles loading API keys and settings from environment variables and config files
# It provides a clean interface for other parts of the application to access configuration

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass

# Import python-dotenv to load .env files
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """
    Configuration class for the Bot Detector application
    
    This class loads configuration from multiple sources in order of priority:
    1. Environment variables (highest priority)
    2. config.json file in the same directory
    3. Default values (lowest priority)
    
    This approach allows for flexible deployment while keeping sensitive data secure.
    """
    
    def __init__(self, config_file_path: Optional[str] = None, env_file_path: Optional[str] = None):
        """
        Initialize configuration by loading from various sources
        
        Args:
            config_file_path: Optional path to config JSON file
                             If None, looks for config.json in the current directory
            env_file_path: Optional path to .env file
                          If None, looks for .env in the current directory
        """
        # Set default config file path
        if config_file_path is None:
            config_file_path = Path(__file__).parent / "config.json"
        
        # Set default .env file path - also check for .env folder with config.json
        if env_file_path is None:
            # Check multiple possible locations for .env configuration
            possible_env_paths = [
                Path(__file__).parent / ".env",  # Standard .env file
                Path(__file__).parent / ".env" / "config.json",  # .env folder with config.json
                Path(__file__).parent.parent / ".env" / "config.json",  # .env folder in parent directory
                Path(__file__).parent.parent / ".env"  # .env file in parent directory
            ]
            
            # Use the first one that exists, or default to standard .env
            env_file_path = possible_env_paths[0]  # Default
            for path in possible_env_paths:
                if path.exists():
                    env_file_path = path
                    break
        
        self.config_file_path = Path(config_file_path)
        self.env_file_path = Path(env_file_path)
        
        # Load configuration from .env file first, then JSON file, then environment variables
        # This gives priority: Environment Variables > JSON File > .env File
        self._load_from_env_file()
        self._load_from_file()
        self._load_from_environment()
        
        # Validate that we have some way to access Bluesky or LLMs
        self._validate_configuration()
    
    def _load_from_env_file(self):
        """
        Load configuration from .env file or .env/config.json folder
        
        Supports two formats:
        1. Standard .env file with key=value pairs:
           BLUESKY_USERNAME=your-username
           BLUESKY_PASSWORD=your-password
           OPENAI_API_KEY=sk-...
           
        2. .env folder containing config.json:
           .env/config.json with standard JSON structure
        
        This method loads the configuration and sets environment variables,
        which will then be read by _load_from_environment()
        """
        try:
            if self.env_file_path.exists():
                if self.env_file_path.name == "config.json" and self.env_file_path.parent.name == ".env":
                    # This is a .env/config.json setup
                    logger.info(f"Found .env folder with config.json at {self.env_file_path}")
                    self._load_from_env_config_json()
                elif self.env_file_path.suffix == "" and self.env_file_path.name == ".env":
                    # This is a standard .env file
                    if load_dotenv is not None:
                        load_dotenv(self.env_file_path)
                        logger.info(f"Loaded .env file from {self.env_file_path}")
                    else:
                        logger.warning("python-dotenv not installed, cannot load .env file")
                        logger.info("Install with: pip install python-dotenv")
                else:
                    logger.debug(f"Unrecognized .env format at {self.env_file_path}")
            else:
                logger.debug(f"No .env configuration found at {self.env_file_path}")
                
        except Exception as e:
            logger.warning(f"Error loading .env configuration: {e}")
    
    def _load_from_env_config_json(self):
        """
        Load configuration from .env/config.json and set as environment variables
        This allows the .env folder approach to work with the existing environment variable system
        """
        try:
            with open(self.env_file_path, 'r') as f:
                config_data = json.load(f)
            
            # Convert JSON config to environment variables
            bluesky_config = config_data.get('bluesky', {})
            if bluesky_config.get('username'):
                os.environ['BLUESKY_USERNAME'] = bluesky_config['username']
            if bluesky_config.get('password'):
                os.environ['BLUESKY_PASSWORD'] = bluesky_config['password']
            
            llm_config = config_data.get('llm', {})
            if llm_config.get('openai_api_key'):
                os.environ['OPENAI_API_KEY'] = llm_config['openai_api_key']
            if llm_config.get('anthropic_api_key'):
                os.environ['ANTHROPIC_API_KEY'] = llm_config['anthropic_api_key']
            if llm_config.get('google_api_key'):
                os.environ['GOOGLE_API_KEY'] = llm_config['google_api_key']
            if llm_config.get('preferred_provider'):
                os.environ['PREFERRED_LLM_PROVIDER'] = llm_config['preferred_provider']
            
            api_config = config_data.get('api', {})
            if api_config.get('host'):
                os.environ['API_HOST'] = api_config['host']
            if api_config.get('port'):
                os.environ['API_PORT'] = str(api_config['port'])
            if api_config.get('debug'):
                os.environ['DEBUG_MODE'] = str(api_config['debug']).lower()
            
            logger.info(f"Loaded configuration from .env/config.json")
            
        except Exception as e:
            logger.error(f"Error loading .env/config.json: {e}")
    
    def _load_from_file(self):
        """
        Load configuration from JSON file if it exists
        
        The config.json file should look like this:
        {
            "bluesky": {
                "username": "your-username",
                "password": "your-password"
            },
            "llm": {
                "openai_api_key": "sk-...",
                "anthropic_api_key": "sk-ant-...",
                "google_api_key": "...",
                "preferred_provider": "openai"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": false
            }
        }
        """
        # Initialize with default values
        self.bluesky_username = None
        self.bluesky_password = None
        self.openai_api_key = None
        self.anthropic_api_key = None
        self.google_api_key = None
        self.preferred_llm_provider = None
        self.api_host = "0.0.0.0"
        self.api_port = 8000
        self.debug_mode = False
        
        try:
            if self.config_file_path.exists():
                logger.info(f"Loading configuration from {self.config_file_path}")
                
                with open(self.config_file_path, 'r') as f:
                    config_data = json.load(f)
                
                # Load Bluesky configuration
                bluesky_config = config_data.get('bluesky', {})
                self.bluesky_username = bluesky_config.get('username')
                self.bluesky_password = bluesky_config.get('password')
                
                # Load LLM configuration
                llm_config = config_data.get('llm', {})
                self.openai_api_key = llm_config.get('openai_api_key')
                self.anthropic_api_key = llm_config.get('anthropic_api_key')
                self.google_api_key = llm_config.get('google_api_key')
                self.preferred_llm_provider = llm_config.get('preferred_provider')
                
                # Load API server configuration
                api_config = config_data.get('api', {})
                self.api_host = api_config.get('host', self.api_host)
                self.api_port = api_config.get('port', self.api_port)
                self.debug_mode = api_config.get('debug', self.debug_mode)
                
                logger.info("Configuration loaded from file successfully")
                
            else:
                logger.info("No config file found, using environment variables and defaults")
                
        except Exception as e:
            logger.warning(f"Error loading config file: {e}")
            logger.info("Falling back to environment variables and defaults")
    
    def _load_from_environment(self):
        """
        Load configuration from environment variables
        Environment variables take precedence over config file values
        
        Expected environment variable names:
        - BLUESKY_USERNAME
        - BLUESKY_PASSWORD
        - OPENAI_API_KEY
        - ANTHROPIC_API_KEY
        - GOOGLE_API_KEY
        - PREFERRED_LLM_PROVIDER
        - API_HOST
        - API_PORT
        - DEBUG_MODE
        """
        try:
            # Bluesky credentials
            if os.getenv('BLUESKY_USERNAME'):
                self.bluesky_username = os.getenv('BLUESKY_USERNAME')
                logger.debug("Loaded Bluesky username from environment")
            
            if os.getenv('BLUESKY_PASSWORD'):
                self.bluesky_password = os.getenv('BLUESKY_PASSWORD')
                logger.debug("Loaded Bluesky password from environment")
            
            # LLM API keys
            if os.getenv('OPENAI_API_KEY'):
                self.openai_api_key = os.getenv('OPENAI_API_KEY')
                logger.debug("Loaded OpenAI API key from environment")
            
            if os.getenv('ANTHROPIC_API_KEY'):
                self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
                logger.debug("Loaded Anthropic API key from environment")
            
            if os.getenv('GOOGLE_API_KEY'):
                self.google_api_key = os.getenv('GOOGLE_API_KEY')
                logger.debug("Loaded Google API key from environment")
            
            if os.getenv('PREFERRED_LLM_PROVIDER'):
                self.preferred_llm_provider = os.getenv('PREFERRED_LLM_PROVIDER')
                logger.debug(f"Loaded preferred LLM provider from environment: {self.preferred_llm_provider}")
            
            # API server configuration
            if os.getenv('API_HOST'):
                self.api_host = os.getenv('API_HOST')
            
            if os.getenv('API_PORT'):
                try:
                    self.api_port = int(os.getenv('API_PORT'))
                except ValueError:
                    logger.warning("Invalid API_PORT in environment, using default")
            
            if os.getenv('DEBUG_MODE'):
                self.debug_mode = os.getenv('DEBUG_MODE').lower() in ('true', '1', 'yes', 'on')
            
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
    
    def _validate_configuration(self):
        """
        Validate that we have enough configuration to run the application
        
        At minimum, we need either:
        - Bluesky credentials (for fetching data), OR
        - At least one LLM API key (for analysis)
        
        Ideally we have both, but the system should work with limited capabilities.
        """
        has_bluesky = bool(self.bluesky_username and self.bluesky_password)
        has_llm = bool(self.openai_api_key or self.anthropic_api_key or self.google_api_key)
        
        if not has_bluesky and not has_llm:
            logger.warning("No Bluesky credentials or LLM API keys found!")
            logger.warning("The application will have limited functionality.")
            logger.warning("Please set up credentials in config.json or environment variables.")
        
        if not has_bluesky:
            logger.warning("No Bluesky credentials found. Data fetching will be limited.")
            logger.info("Set BLUESKY_USERNAME and BLUESKY_PASSWORD to enable full functionality.")
        
        if not has_llm:
            logger.warning("No LLM API keys found. AI-powered analysis will be unavailable.")
            logger.info("Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")
        
        # Log what capabilities we have
        capabilities = []
        if has_bluesky:
            capabilities.append("Bluesky data fetching")
        if has_llm:
            available_llms = []
            if self.openai_api_key:
                available_llms.append("OpenAI")
            if self.anthropic_api_key:
                available_llms.append("Anthropic")
            if self.google_api_key:
                available_llms.append("Google")
            capabilities.append(f"LLM analysis ({', '.join(available_llms)})")
        
        if capabilities:
            logger.info(f"Application capabilities: {', '.join(capabilities)}")
        else:
            logger.warning("Application has no configured capabilities!")
    
    def has_bluesky_credentials(self) -> bool:
        """Check if Bluesky credentials are configured"""
        return bool(self.bluesky_username and self.bluesky_password)
    
    def has_llm_keys(self) -> bool:
        """Check if any LLM API keys are configured"""
        return bool(
            self.openai_api_key or 
            self.anthropic_api_key or 
            self.google_api_key
        )
    
    def get_llm_keys(self) -> Dict[str, str]:
        """
        Get a dictionary of available LLM API keys
        
        Returns:
            Dictionary mapping provider names to API keys
            Only includes keys that are actually configured
        """
        keys = {}
        
        if self.openai_api_key:
            keys['openai'] = self.openai_api_key
        
        if self.anthropic_api_key:
            keys['anthropic'] = self.anthropic_api_key
        
        if self.google_api_key:
            keys['google'] = self.google_api_key
        
        return keys
    
    def create_example_config_file(self) -> str:
        """
        Create an example configuration file
        
        Returns:
            The path to the created example file
            
        This is useful for first-time setup
        """
        example_config = {
            "bluesky": {
                "username": "your-bluesky-username-or-email",
                "password": "your-bluesky-password"
            },
            "llm": {
                "openai_api_key": "sk-your-openai-key-here",
                "anthropic_api_key": "sk-ant-your-anthropic-key-here", 
                "google_api_key": "your-google-api-key-here",
                "preferred_provider": "openai"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            }
        }
        
        example_path = self.config_file_path.parent / "config.example.json"
        
        try:
            with open(example_path, 'w') as f:
                json.dump(example_config, f, indent=2)
            
            logger.info(f"Created example config file: {example_path}")
            return str(example_path)
            
        except Exception as e:
            logger.error(f"Failed to create example config: {e}")
            return ""
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration (safe for logging)
        
        Returns:
            Dictionary with configuration summary (no sensitive data)
        """
        return {
            "bluesky_configured": self.has_bluesky_credentials(),
            "llm_providers": list(self.get_llm_keys().keys()),
            "preferred_llm": self.preferred_llm_provider,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "debug_mode": self.debug_mode,
            "config_file_exists": self.config_file_path.exists()
        }