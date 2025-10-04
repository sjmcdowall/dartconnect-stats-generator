"""Configuration handling for DartConnect Statistics Generator."""

import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Handles application configuration from YAML files."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            # Return default configuration if file doesn't exist
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Merge with defaults to ensure all required keys exist
            default_config = self._get_default_config()
            return self._merge_configs(default_config, config)
            
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {self.config_path}: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'data_processing': {
                'date_format': '%Y-%m-%d',
                'decimal_places': 2,
                'min_games_threshold': 5
            },
            'pdf_reports': {
                'report1': {
                    'title': 'League Statistics Report',
                    'page_size': 'A4',
                    'font_family': 'Helvetica',
                    'font_size': 10,
                    'include_charts': True
                },
                'report2': {
                    'title': 'Player Performance Report',
                    'page_size': 'A4',
                    'font_family': 'Helvetica',
                    'font_size': 10,
                    'include_charts': True
                }
            },
            'statistics': {
                'calculate_averages': True,
                'calculate_percentiles': True,
                'calculate_trends': True,
                'rolling_window_games': 10
            }
        }
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with default config."""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'pdf_reports.report1.title')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_data_processing_config(self) -> Dict[str, Any]:
        """Get data processing configuration."""
        return self._config.get('data_processing', {})
    
    def get_pdf_config(self, report_name: str) -> Dict[str, Any]:
        """Get PDF configuration for specific report."""
        return self._config.get('pdf_reports', {}).get(report_name, {})
    
    def get_statistics_config(self) -> Dict[str, Any]:
        """Get statistics calculation configuration."""
        return self._config.get('statistics', {})