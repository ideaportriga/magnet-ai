"""
Tests for security module - provider-only fields protection.
"""

import pytest

from services.knowledge_sources.security import (
    PROVIDER_ONLY_FIELDS,
    filter_provider_only_fields,
    is_provider_only_field,
)


class TestProviderOnlyFields:
    """Tests for provider-only field security checks"""

    def test_provider_only_fields_contains_critical_fields(self):
        """Verify that all critical security fields are in PROVIDER_ONLY_FIELDS"""
        critical_fields = {
            'endpoint',
            'client_id',
            'client_secret',
            'username',
            'password',
            'token',
            'api_key',
        }
        
        assert critical_fields.issubset(PROVIDER_ONLY_FIELDS), \
            "All critical security fields must be in PROVIDER_ONLY_FIELDS"

    def test_is_provider_only_field_security_fields(self):
        """Test that security-critical fields are correctly identified"""
        assert is_provider_only_field('endpoint')
        assert is_provider_only_field('client_id')
        assert is_provider_only_field('client_secret')
        assert is_provider_only_field('password')
        assert is_provider_only_field('api_key')

    def test_is_provider_only_field_non_security_fields(self):
        """Test that non-security fields are not flagged"""
        assert not is_provider_only_field('site_path')
        assert not is_provider_only_field('library')
        assert not is_provider_only_field('recursive')
        assert not is_provider_only_field('page_name')

    def test_filter_provider_only_fields_removes_security_fields(self):
        """Test that security fields are removed from configuration"""
        config = {
            'endpoint': 'https://example.com',
            'client_id': 'secret_id',
            'client_secret': 'secret_value',
            'site_path': 'sites/MyBusiness',
            'library': 'Documents',
            'recursive': True,
        }
        
        filtered = filter_provider_only_fields(config)
        
        # Security fields should be removed
        assert 'endpoint' not in filtered
        assert 'client_id' not in filtered
        assert 'client_secret' not in filtered
        
        # Non-security fields should remain
        assert filtered['site_path'] == 'sites/MyBusiness'
        assert filtered['library'] == 'Documents'
        assert filtered['recursive'] is True

    def test_filter_provider_only_fields_empty_config(self):
        """Test filtering empty configuration"""
        assert filter_provider_only_fields({}) == {}

    def test_filter_provider_only_fields_only_security_fields(self):
        """Test configuration with only security fields results in empty dict"""
        config = {
            'endpoint': 'https://example.com',
            'client_id': 'id',
            'api_key': 'key',
        }
        
        assert filter_provider_only_fields(config) == {}

    def test_filter_provider_only_fields_preserves_non_security_fields(self):
        """Test that non-security fields are preserved exactly"""
        config = {
            'site_path': 'sites/MyBusiness',
            'library': 'Documents',
            'recursive': True,
            'page_name': 'HomePage',
            'embed_title': False,
        }
        
        filtered = filter_provider_only_fields(config)
        
        assert filtered == config

    def test_provider_only_fields_immutable(self):
        """Test that PROVIDER_ONLY_FIELDS is immutable (frozenset)"""
        assert isinstance(PROVIDER_ONLY_FIELDS, frozenset)
        
        with pytest.raises(AttributeError):
            PROVIDER_ONLY_FIELDS.add('new_field')  # type: ignore
