"""
Input validation and sanitization service for user inputs
"""
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

class ValidationResult:
    """Result of validation operation"""
    def __init__(self, is_valid: bool, cleaned_value: Any = None, error_message: str = None):
        self.is_valid = is_valid
        self.cleaned_value = cleaned_value
        self.error_message = error_message

class InputValidationService:
    """Service for comprehensive input validation and sanitization"""
    
    # Harmful characters pattern as specified in design
    HARMFUL_CHARS_PATTERN = r'[<>{}[\]\\`~|@#$%^&*()+=]'
    
    # Additional patterns for enhanced security
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(--|#|/\*|\*/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)'
    ]
    
    # Spam/low-quality content patterns
    SPAM_PATTERNS = [
        r'^(.)\1{10,}$',  # Repeated characters
        r'^[^a-zA-Z0-9]*$',  # Only special characters
        r'^\s*$',  # Only whitespace
        r'^(.{1,3})\1{5,}$'  # Repeated short patterns
    ]
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Remove potentially harmful characters from input
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text with harmful characters removed
        """
        if not text:
            return ""
        
        # Remove harmful characters and extra whitespace
        cleaned = re.sub(cls.HARMFUL_CHARS_PATTERN, '', text.strip())
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    @classmethod
    def check_content_safety(cls, text: str) -> bool:
        """
        Check if content is safe (no XSS patterns, SQL injection, meaningful content)
        
        Args:
            text: Text to check for safety
            
        Returns:
            True if content is safe, False otherwise
        """
        if not text:
            return False
        
        # Check for XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'vbscript:',
            r'data:text/html'
        ]
        
        text_lower = text.lower()
        
        # Check XSS patterns
        for pattern in xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return False
        
        # Check SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Check for spam patterns
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    @classmethod
    def validate_problem_description(cls, text: str) -> ValidationResult:
        """
        Validate problem description with comprehensive checks
        
        Args:
            text: Problem description to validate
            
        Returns:
            ValidationResult with validation status and cleaned text
        """
        if not text or not text.strip():
            return ValidationResult(False, None, 'Problem description cannot be empty')
        
        # Length validation before processing (requirement 4.1)
        if len(text.strip()) < 10:
            return ValidationResult(False, None, 'Problem description must be at least 10 characters long')
        
        if len(text.strip()) > 1000:
            return ValidationResult(False, None, 'Problem description cannot exceed 1000 characters')
        
        # Check content safety first (requirement 4.2)
        if not cls.check_content_safety(text):
            return ValidationResult(False, None, 'Problem description contains unsafe or potentially harmful content. Please remove any scripts, special characters, or suspicious patterns.')
        
        # Sanitize input (requirement 4.2)
        cleaned = cls.sanitize_input(text)
        
        # Check for meaningful content after sanitization (requirement 4.3)
        if not re.search(r'[a-zA-Z0-9]', cleaned):
            return ValidationResult(False, None, 'Problem description must contain meaningful alphanumeric content, not just whitespace or special characters')
        
        # Check minimum word count for meaningful content
        words = [word for word in cleaned.split() if len(word) > 1]  # Filter out single characters
        if len(words) < 3:
            return ValidationResult(False, None, 'Problem description must contain at least 3 meaningful words')
        
        # Additional quality checks
        if len(cleaned) < 10:  # After cleaning, still check minimum length
            return ValidationResult(False, None, 'Problem description is too short after removing invalid characters. Please provide more detailed information.')
        
        return ValidationResult(True, cleaned, None)
    
    @classmethod
    def validate_optional_field(cls, value: Optional[str], field_name: str = "field", max_length: int = 100) -> ValidationResult:
        """
        Validate optional fields like domain, region, target_audience
        
        Args:
            value: Field value to validate
            field_name: Name of the field for error messages
            max_length: Maximum allowed length
            
        Returns:
            ValidationResult with validation status and cleaned value
        """
        if not value or not value.strip():
            return ValidationResult(True, None, None)
        
        # Check content safety
        if not cls.check_content_safety(value):
            return ValidationResult(False, None, f'{field_name} contains unsafe content')
        
        # Sanitize input
        cleaned = cls.sanitize_input(value)
        
        if len(cleaned) > max_length:
            return ValidationResult(False, None, f'{field_name} cannot exceed {max_length} characters')
        
        # Return None if cleaned value is empty after sanitization
        return ValidationResult(True, cleaned if cleaned else None, None)
    
    @classmethod
    def validate_input_data(cls, problem_description: str, domain: Optional[str] = None, 
                          region: Optional[str] = None, target_audience: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate all input data at once
        
        Args:
            problem_description: Main problem description
            domain: Optional domain field
            region: Optional region field
            target_audience: Optional target audience field
            
        Returns:
            Dictionary with validation results and cleaned data
        """
        results = {
            'is_valid': True,
            'errors': [],
            'cleaned_data': {}
        }
        
        # Validate problem description
        desc_result = cls.validate_problem_description(problem_description)
        if not desc_result.is_valid:
            results['is_valid'] = False
            results['errors'].append(desc_result.error_message)
        else:
            results['cleaned_data']['problem_description'] = desc_result.cleaned_value
        
        # Validate optional fields
        for field_name, field_value in [('domain', domain), ('region', region), ('target_audience', target_audience)]:
            field_result = cls.validate_optional_field(field_value, field_name)
            if not field_result.is_valid:
                results['is_valid'] = False
                results['errors'].append(field_result.error_message)
            else:
                results['cleaned_data'][field_name] = field_result.cleaned_value
        
        return results
    
    @classmethod
    def get_validation_errors_details(cls, errors: List[str]) -> Dict[str, Any]:
        """
        Provide detailed error information with suggestions for fixing validation issues
        
        Args:
            errors: List of validation error messages
            
        Returns:
            Dictionary with detailed error information and suggestions
        """
        error_details = {
            'total_errors': len(errors),
            'errors': errors,
            'suggestions': []
        }
        
        # Provide specific suggestions based on error types
        for error in errors:
            if 'at least 10 characters' in error:
                error_details['suggestions'].append('Please provide a more detailed description of your problem or need')
            elif 'exceed 1000 characters' in error:
                error_details['suggestions'].append('Please shorten your description to focus on the main problem')
            elif 'unsafe' in error or 'harmful' in error:
                error_details['suggestions'].append('Please remove any HTML tags, scripts, or special characters from your input')
            elif 'meaningful' in error:
                error_details['suggestions'].append('Please use regular words and sentences to describe your problem')
            elif '3 meaningful words' in error:
                error_details['suggestions'].append('Please provide more context about what you are trying to solve')
        
        # Remove duplicate suggestions
        error_details['suggestions'] = list(set(error_details['suggestions']))
        
        return error_details
    
    @classmethod
    def sanitize_and_validate_batch(cls, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple inputs at once for batch processing
        
        Args:
            inputs: List of input dictionaries with problem_description and optional fields
            
        Returns:
            Dictionary with batch validation results
        """
        results = {
            'total_inputs': len(inputs),
            'valid_inputs': [],
            'invalid_inputs': [],
            'validation_summary': {
                'passed': 0,
                'failed': 0,
                'common_errors': {}
            }
        }
        
        for i, input_data in enumerate(inputs):
            problem_desc = input_data.get('problem_description', '')
            domain = input_data.get('domain')
            region = input_data.get('region')
            target_audience = input_data.get('target_audience')
            
            validation_result = cls.validate_input_data(problem_desc, domain, region, target_audience)
            
            input_result = {
                'index': i,
                'original_data': input_data,
                'validation_result': validation_result
            }
            
            if validation_result['is_valid']:
                results['valid_inputs'].append(input_result)
                results['validation_summary']['passed'] += 1
            else:
                results['invalid_inputs'].append(input_result)
                results['validation_summary']['failed'] += 1
                
                # Track common errors
                for error in validation_result['errors']:
                    error_key = error.split('.')[0] if '.' in error else error[:50]  # First part of error
                    results['validation_summary']['common_errors'][error_key] = \
                        results['validation_summary']['common_errors'].get(error_key, 0) + 1
        
        return results
    
    @classmethod
    def is_likely_spam_or_test(cls, text: str) -> bool:
        """
        Detect if input is likely spam or test content
        
        Args:
            text: Text to check
            
        Returns:
            True if likely spam/test, False otherwise
        """
        if not text:
            return True
        
        text_lower = text.lower().strip()
        
        # Common test patterns
        test_patterns = [
            r'^test\s*$',
            r'^testing\s*$',
            r'^hello\s*$',
            r'^hi\s*$',
            r'^abc+\s*$',
            r'^123+\s*$',
            r'^(test|testing|hello|hi)\s+(test|testing|hello|hi)',
            r'^[a-z]\s*$',  # Single letter
            r'^(asdf|qwerty|lorem ipsum)',
        ]
        
        for pattern in test_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check for very repetitive content
        words = text_lower.split()
        if len(words) > 2:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
                return True
        
        return False