import json
import re
from datetime import datetime
from dateutil import parser as date_parser
from typing import Dict, Tuple, Any, Optional, List

class SchemaConfigLoader:
    """Load and manage schema configurations from JSON"""
    
    @staticmethod
    def load_config(filepath='schema_config.json'):
        """Load schema config from JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Schema config file not found: {filepath}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in schema config: {e}")
    
    @staticmethod
    def get_client_config(config: Dict, client_id: str) -> Dict:
        """Get config for specific client, fallback to default"""
        return config['clients'].get(client_id, config['clients']['default'])

class SchemaValidator:
    """Validate field values against schema rules"""
    
    @staticmethod
    def validate_field(field_name: str, value: Any, rules: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate a field value against rules
        Returns: (is_valid, error_message)
        """
        if not rules:
            return True, None
        
        # Check type
        expected_type = rules.get('type')
        if expected_type and not SchemaValidator._check_type(value, expected_type):
            return False, f"Field '{field_name}' has invalid type. Expected {expected_type}, got {type(value).__name__}"
        
        # Check numeric constraints
        if 'min' in rules and isinstance(value, (int, float)):
            if value < rules['min']:
                return False, f"Field '{field_name}' is below minimum: {rules['min']}"
        
        if 'max' in rules and isinstance(value, (int, float)):
            if value > rules['max']:
                return False, f"Field '{field_name}' exceeds maximum: {rules['max']}"
        
        # Check string constraints
        if isinstance(value, str):
            if 'min_length' in rules and len(value) < rules['min_length']:
                return False, f"Field '{field_name}' is too short (min: {rules['min_length']})"
            
            if 'max_length' in rules and len(value) > rules['max_length']:
                return False, f"Field '{field_name}' is too long (max: {rules['max_length']})"
            
            if 'pattern' in rules:
                if not re.match(rules['pattern'], value):
                    return False, f"Field '{field_name}' does not match required pattern: {rules['pattern']}"
        
        return True, None
    
    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type (supports 'string|number')"""
        if '|' in expected_type:
            types = [t.strip() for t in expected_type.split('|')]
            return any(SchemaValidator._check_type(value, t) for t in types)
        
        type_map = {
            'string': str,
            'number': (int, float),
            'float': float,
            'int': int,
            'boolean': bool,
            'datetime': datetime,
        }
        
        expected = type_map.get(expected_type, str)
        return isinstance(value, expected)

class NestedFieldExtractor:
    """Extract values from nested objects (e.g., 'metrics.name')"""
    
    @staticmethod
    def get_nested(obj: Dict, path: str) -> Optional[Any]:
        """
        Get value from nested dictionary using dot notation
        Example: get_nested({'a': {'b': 'value'}}, 'a.b') -> 'value'
        """
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None
        
        return current

class DateTimeParser:
    """Parse datetime from various formats"""
    
    @staticmethod
    def parse(value: Any, allowed_formats: List[str]) -> Optional[str]:
        """
        Parse datetime value to ISO format
        Returns: ISO 8601 string or None if parsing fails
        """
        if isinstance(value, datetime):
            return value.isoformat() + 'Z' if not value.tzinfo else value.isoformat()
        
        if not isinstance(value, str):
            return None
        
        # Try unix timestamp
        if 'unix' in allowed_formats:
            try:
                timestamp = float(value)
                if 'unix_ms' in allowed_formats and timestamp > 1e10:
                    timestamp /= 1000
                dt = datetime.utcfromtimestamp(timestamp)
                return dt.isoformat() + 'Z'
            except (ValueError, OSError):
                pass
        
        # Try dateutil parser for flexible parsing
        try:
            dt = date_parser.parse(value)
            return dt.isoformat() + 'Z' if not dt.tzinfo else dt.isoformat()
        except:
            pass
        
        return None

class EnhancedNormalizer:
    """
    Advanced normalizer using schema configuration
    Supports:
    - Client-specific field mappings
    - Type conversions
    - Nested field extraction
    - Validation rules
    """
    
    def __init__(self, schema_config: Dict):
        self.schema_config = schema_config
        self.validator = SchemaValidator()
        self.datetime_parser = DateTimeParser()
    
    def normalize(self, raw_event: Dict) -> Tuple[Optional[Dict], List[str]]:
        """
        Normalize raw event using schema config
        Returns: (normalized_dict, error_list)
        """
        try:
            source = raw_event.get('source', 'unknown')
            payload = raw_event.get('payload', {})
            
            client_config = SchemaConfigLoader.get_client_config(self.schema_config, source)
            
            normalized = {
                'client_id': source,
                'metric': None,
                'amount': None,
                'timestamp': None,
            }
            
            errors = []
            field_mapping = client_config['field_mapping']
            validation_rules = client_config.get('validation_rules', {})
            timestamp_formats = self.schema_config['global_settings']['timestamp_formats']
            
            # Extract and convert each required field
            for canonical_field, raw_field_path in field_mapping.items():
                raw_value = NestedFieldExtractor.get_nested(payload, raw_field_path)
                
                if raw_value is None:
                    errors.append(f"Missing required field: '{raw_field_path}' (maps to '{canonical_field}')")
                    continue
                
                # Validate against rules
                if raw_field_path in validation_rules:
                    is_valid, error_msg = self.validator.validate_field(
                        raw_field_path,
                        raw_value,
                        validation_rules[raw_field_path]
                    )
                    if not is_valid:
                        errors.append(error_msg)
                        continue
                
                # Convert based on field type
                if canonical_field == 'amount':
                    normalized['amount'] = self._convert_to_float(raw_value)
                    if normalized['amount'] is None:
                        errors.append(f"Cannot convert '{canonical_field}' to number: {raw_value}")
                
                elif canonical_field == 'timestamp':
                    normalized['timestamp'] = self.datetime_parser.parse(raw_value, timestamp_formats)
                    if normalized['timestamp'] is None:
                        errors.append(f"Cannot parse '{canonical_field}' as datetime: {raw_value}")
                
                else:  # metric or other string field
                    normalized[canonical_field] = str(raw_value)
            
            # Return errors if any critical field failed
            if errors:
                return None, errors
            
            # Validate all required fields are present
            if normalized['metric'] is None:
                errors.append("Missing metric field")
            if normalized['amount'] is None:
                errors.append("Missing amount field")
            if normalized['timestamp'] is None:
                errors.append("Missing timestamp field")
            
            if errors:
                return None, errors
            
            return normalized, []
        
        except Exception as e:
            return None, [f"Unexpected normalization error: {str(e)}"]
    
    @staticmethod
    def _convert_to_float(value: Any) -> Optional[float]:
        """Convert value to float, handling various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        
        return None

# Backwards compatibility
class Normalizer(EnhancedNormalizer):
    """Legacy name for backwards compatibility"""
    pass