import yaml

class ConfigError(Exception): # Define ConfigError
    """Custom exception class for configuration errors."""
    pass

class Config:
    def __init__(self, config_path):
        print(f"Config path inside Config class: {config_path}") # Print path in Config class
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {config_path}") # Use ConfigError
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML configuration: {e}") # Use ConfigError

    def __getitem__(self, key):
        if key not in self.config:
            raise ConfigError(f"Configuration key not found: {key}") # Use ConfigError
        return self.config[key]
