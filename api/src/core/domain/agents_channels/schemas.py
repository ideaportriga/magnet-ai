"""
Pydantic schemas for agents channels validation.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from utils.secrets import encrypt_string, decrypt_string




class WebChannel(BaseModel):
    """Web channel schema."""
    enabled: bool = Field(default=False, description="Web channel enabled")
    theme: str = Field(default="siebel", description="Web channel theme")
    show_close_button: bool = Field(default=False, description="Web channel show close button")
    is_icon_hide: bool = Field(default=False, description="Web channel hide icon")

class WebChannelUpdate(WebChannel):
    """Web channel update schema."""
    pass

class MsTeamsChannelBase(BaseModel):
    """MS Teams channel base schema."""
    enabled: bool = Field(default=False, description="MS Teams channel enabled")
    client_id: str = Field(default="", description="MS Teams client ID")
    tenant_id: str = Field(default="", description="MS Teams tenant ID")

class MsTeamsChannel(MsTeamsChannelBase):   
    """MS Teams channel schema."""
    secret_value_encrypted: str = Field(default=None, alias="secret_value", description="MS Teams secret value encrypted")

class MsTeamsChannelUpdate(MsTeamsChannelBase):
    """MS Teams channel update schema."""
    secret_value: Optional[str] = Field(default=None, description="MS Teams secret value")
    #encrypted are only used for validation, not saved to database
    secret_value_encrypted: Optional[str] = Field(default=None, exclude=True, description="MS Teams secret value encrypted (used when secret_value is empty, not saved)")
    
    @model_validator(mode="after")
    def encrypt_secret_value(self):
        """Use secret_value_encrypted if secret_value is None or empty."""
        if self.secret_value is None:
            if self.secret_value_encrypted:
                # Use the existing encrypted value
                self.secret_value = self.secret_value_encrypted
            else:
                self.secret_value = None
        elif self.secret_value == "":
            self.secret_value = None
        else:
            # Encrypt the new secret value
            try:
                self.secret_value = encrypt_string(self.secret_value)
            except ValueError as e:
                raise ValueError(f"Failed to encrypt secret value: {str(e)}") from e
        
        return self


class SlackChannelBase(BaseModel):
    """Slack channel base schema."""
    enabled: bool = Field(default=False, description="Slack channel enabled")
    client_id: str = Field(default=None, description="Slack client ID")
    agent_scopes: str = Field(default=None, description="Slack agent scopes")

class SlackChannel(SlackChannelBase):
    """Slack channel schema."""
    token_encrypted: str = Field(default=None, alias="token", description="Slack token encrypted")
    signing_secret_encrypted: str = Field(default=None, alias="signing_secret", description="Slack signing secret encrypted")
    client_secret_encrypted: str = Field(default=None, alias="client_secret", description="Slack client secret encrypted")
    state_secret_encrypted: str = Field(default=None, alias="state_secret", description="Slack state secret encrypted")

class SlackChannelUpdate(SlackChannelBase):
    """Slack channel update schema."""
    token: Optional[str] = Field(default=None, description="Slack token")
    signing_secret: Optional[str] = Field(default=None, description="Slack signing secret")
    client_secret: Optional[str] = Field(default=None, description="Slack client secret")
    state_secret: Optional[str] = Field(default=None, description="Slack state secret")
    #encrypted are only used for validation, not saved to database
    token_encrypted: Optional[str] = Field(default=None, exclude=True, description="Slack token encrypted")
    signing_secret_encrypted: Optional[str] = Field(default=None, exclude=True, description="Slack signing secret encrypted")
    client_secret_encrypted: Optional[str] = Field(default=None, exclude=True, description="Slack client secret encrypted")
    state_secret_encrypted: Optional[str] = Field(default=None, exclude=True, description="Slack state secret encrypted")
    @model_validator(mode="after")
    def encrypt_secrets(self):
        """Encrypt secrets before sending to database."""
        secret_fields = ["token", "signing_secret", "client_secret", "state_secret"]
        
        for field_name in secret_fields:
            value = getattr(self, field_name)
            encrypted_field_name = f"{field_name}_encrypted"
            encrypted_value = getattr(self, encrypted_field_name, None)
            
            if value is None:
                # Use existing encrypted value if available
                setattr(self, field_name, encrypted_value if encrypted_value else None)
            elif value == "":
                setattr(self, field_name, None)
            else:
                # Encrypt the new value
                try:
                    setattr(self, field_name, encrypt_string(value))
                except ValueError as e:
                    raise ValueError(f"Failed to encrypt {field_name}: {str(e)}") from e
        
        return self



class AgentChannels(BaseModel):
    """Agent channels schema."""

    # temporarily allow extra fields
    model_config = ConfigDict(extra="allow")
    
    web: Optional[WebChannel] = Field(default=None, description="Web channel configuration")
    ms_teams: Optional[MsTeamsChannel] = Field(default=None, description="MS Teams channel configuration")
    slack: Optional[SlackChannel] = Field(default=None, description="Slack channel configuration")

class AgentChannelsUpdate(BaseModel):
    """Agent channels update schema."""

    # temporarily allow extra fields
    model_config = ConfigDict(extra="allow")
    
    web: Optional[WebChannelUpdate] = Field(default=None, description="Web channel configuration")
    ms_teams: Optional[MsTeamsChannelUpdate] = Field(default=None, description="MS Teams channel configuration")
    slack: Optional[SlackChannelUpdate] = Field(default=None, description="Slack channel configuration")