#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security validators for input sanitization and validation
Prevents XSS attacks and ensures data integrity
"""

import re
import html
import bleach
from flask import abort
from functools import wraps


class SecurityValidator:
    """Security validation and sanitization utilities"""
    
    # Allowed HTML tags for rich text (none by default for security)
    ALLOWED_TAGS = []
    ALLOWED_ATTRIBUTES = {}
    
    # Maximum field lengths to prevent DoS attacks
    MAX_LENGTHS = {
        'password_name': 100,
        'username': 50,
        'password': 500,  # Encrypted passwords can be longer
        'notes': 1000,
        'url': 500,
        'category': 50,
        'user_name': 100,
        'email': 254  # RFC 5321 compliant
    }
    
    # Regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'url': re.compile(r'^https?://[^\s<>"{}|\\^`\[\]]+$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_\.@!#\$%&\*\+/=\?\^`\{\|\}~]*$')
    }

    @classmethod
    def sanitize_html(cls, text):
        """Remove all HTML tags and entities"""
        if not text:
            return ""
        
        # First escape HTML entities
        text = html.escape(str(text))
        
        # Remove any remaining HTML tags using bleach
        text = bleach.clean(text, tags=cls.ALLOWED_TAGS, attributes=cls.ALLOWED_ATTRIBUTES, strip=True)
        
        return text.strip()

    @classmethod
    def validate_length(cls, text, field_name):
        """Validate field length"""
        if not text:
            return True
            
        max_length = cls.MAX_LENGTHS.get(field_name, 255)
        if len(str(text)) > max_length:
            return False
        
        return True

    @classmethod
    def validate_email(cls, email):
        """Validate email format"""
        if not email:
            return False
        
        email = str(email).strip()
        if not cls.validate_length(email, 'email'):
            return False
            
        return bool(cls.PATTERNS['email'].match(email))

    @classmethod
    def validate_url(cls, url):
        """Validate URL format"""
        if not url:
            return True  # URLs are optional
        
        url = str(url).strip()
        if not cls.validate_length(url, 'url'):
            return False
            
        return bool(cls.PATTERNS['url'].match(url))

    @classmethod
    def validate_safe_string(cls, text, field_name='safe_string'):
        """Validate that string contains only safe characters"""
        if not text:
            return True
        
        text = str(text)
        if not cls.validate_length(text, field_name):
            return False
        
        # Allow most printable characters but block dangerous ones
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
        for char in dangerous_chars:
            if char in text:
                return False
        
        return True

    @classmethod
    def sanitize_input(cls, data, field_name):
        """Comprehensive input sanitization"""
        if not data:
            return ""
        
        # Convert to string and strip whitespace
        sanitized = str(data).strip()
        
        # Apply HTML sanitization
        sanitized = cls.sanitize_html(sanitized)
        
        # Validate length
        if not cls.validate_length(sanitized, field_name):
            raise ValueError(f"Field '{field_name}' exceeds maximum length")
        
        return sanitized


def validate_password_data(f):
    """Decorator to validate password creation/update data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, g
        
        if not request.is_json:
            abort(400, description="Request must be JSON")
        
        data = request.get_json()
        if not data:
            abort(400, description="No data provided")
        
        # Validate and sanitize each field without requiring specific fields
        try:
            # Password name validation (could be 'name' or 'site_name')
            for name_field in ['name', 'site_name']:
                if name_field in data and data[name_field]:
                    if not SecurityValidator.validate_safe_string(data[name_field], 'password_name'):
                        abort(400, description=f"Field '{name_field}' contains invalid characters")
                    data[name_field] = SecurityValidator.sanitize_input(data[name_field], 'password_name')
            
            # Username validation
            if 'username' in data and data['username']:
                if not SecurityValidator.validate_safe_string(data['username'], 'username'):
                    abort(400, description="Username contains invalid characters")
                data['username'] = SecurityValidator.sanitize_input(data['username'], 'username')
            
            # Password validation (don't sanitize, just validate length)
            if 'password' in data and data['password']:
                if not SecurityValidator.validate_length(data['password'], 'password'):
                    abort(400, description="Password is too long")
            
            # Optional fields validation
            for field in ['notes', 'description']:
                if field in data and data[field]:
                    if not SecurityValidator.validate_safe_string(data[field], 'notes'):
                        abort(400, description=f"Field '{field}' contains invalid characters")
                    data[field] = SecurityValidator.sanitize_input(data[field], 'notes')
            
            for field in ['url', 'site_url']:
                if field in data and data[field]:
                    if not SecurityValidator.validate_url(data[field]):
                        abort(400, description=f"Invalid URL format in field '{field}'")
                    data[field] = SecurityValidator.sanitize_input(data[field], 'url')
            
            if 'category' in data and data['category']:
                if not SecurityValidator.validate_safe_string(data['category'], 'category'):
                    abort(400, description="Category contains invalid characters")
                data['category'] = SecurityValidator.sanitize_input(data['category'], 'category')
                
        except ValueError as e:
            abort(400, description=str(e))
        
        # Store sanitized data in Flask's g object for the decorated function to use
        g.validated_data = data
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_user_data(f):
    """Decorator to validate user registration/update data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, g
        
        if not request.is_json:
            abort(400, description="Request must be JSON")
        
        data = request.get_json()
        if not data:
            abort(400, description="No data provided")
        
        try:
            # Email validation
            if 'email' in data:
                if not SecurityValidator.validate_email(data['email']):
                    abort(400, description="Invalid email format")
                data['email'] = SecurityValidator.sanitize_input(data['email'], 'email')
            
            # Name validation
            if 'name' in data and data['name']:
                if not SecurityValidator.validate_safe_string(data['name'], 'user_name'):
                    abort(400, description="Name contains invalid characters")
                data['name'] = SecurityValidator.sanitize_input(data['name'], 'user_name')
            
            # Password validation (for registration)
            if 'password' in data:
                if not SecurityValidator.validate_length(data['password'], 'password'):
                    abort(400, description="Password is too long")
                # Don't sanitize passwords, just validate length
                
        except ValueError as e:
            abort(400, description=str(e))
        
        # Store sanitized data in Flask's g object for the decorated function to use
        g.validated_data = data
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_json_input(f):
    """Generic decorator for JSON input validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, g
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                abort(400, description="Request must be JSON")
            
            data = request.get_json()
            if not data:
                abort(400, description="No data provided")
            
            # Basic sanitization for all string fields
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = SecurityValidator.sanitize_html(value)
            
            # Store sanitized data in Flask's g object
            g.validated_data = data
        
        return f(*args, **kwargs)
    
    return decorated_function