import requests
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class OIDCConfig:
    authorization_endpoint: str
    token_endpoint: str
    scopes_supported: list
    cached_at: datetime

class HubstaffOAuth:
    DISCOVERY_URL = "https://account.hubstaff.com/.well-known/openid-configuration"
    CACHE_DURATION = timedelta(days=7)  # Cache for 1 week as Hubstaff suggests
    
    def __init__(self):
        self._oidc_config: Optional[OIDCConfig] = None
        self._last_fetch: Optional[datetime] = None
    
    def _is_cache_valid(self) -> bool:
        """Check if the cached OIDC config is still valid"""
        if not self._oidc_config or not self._last_fetch:
            return False
        return datetime.now() - self._last_fetch < self.CACHE_DURATION
    
    def _fetch_oidc_config(self) -> OIDCConfig:
        """Fetch OIDC configuration from Hubstaff"""
        try:
            response = requests.get(self.DISCOVERY_URL, timeout=10)
            response.raise_for_status()
            config_data = response.json()
            
            return OIDCConfig(
                authorization_endpoint=config_data["authorization_endpoint"],
                token_endpoint=config_data["token_endpoint"],
                scopes_supported=config_data.get("scopes_supported", []),
                cached_at=datetime.now()
            )
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch OIDC configuration: {e}")
    
    def get_oidc_config(self) -> OIDCConfig:
        """Get OIDC configuration, using cache if valid"""
        if not self._is_cache_valid():
            self._oidc_config = self._fetch_oidc_config()
            self._last_fetch = datetime.now()
        
        return self._oidc_config
    
    def get_auth_url(self, client_id: str, redirect_uri: str, scope: str = "read write") -> str:
        """Generate authorization URL using discovered endpoints"""
        config = self.get_oidc_config()
        
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope
        }
        
        # Build query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{config.authorization_endpoint}?{query_string}"

# Global instance
hubstaff_oauth = HubstaffOAuth() 