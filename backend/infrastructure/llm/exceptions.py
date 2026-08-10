class LLMError(Exception):
    """Base exception for Atlas LLM infrastructure."""


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration is invalid."""


class LLMRateLimitError(LLMError):
    """Raised when the provider reports a rate-limit/quota failure."""


class LLMProviderError(LLMError):
    """Raised when the provider fails for another reason."""


class LLMAllCredentialsExhaustedError(LLMError):
    """Raised when all configured credentials fail."""