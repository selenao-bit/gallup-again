"""Explicit provider selection: Azure credentials never fall back to api.openai.com."""
from openai import OpenAI, AzureOpenAI
from ..config import Settings
from ..services.access import DemoError


def create_client(settings: Settings):
    if not settings.assistant_available:
        message = ('Azure AI needs its private key, resource endpoint and deployment name.'
                   if settings.assistant_mode == 'azure' else 'Live AI is not configured.')
        raise DemoError(503,'assistant_unavailable',message+' Record viewing remains available.')
    if settings.assistant_mode == 'azure':
        return AzureOpenAI(api_key=settings.azure_openai_key.get_secret_value(),
                           azure_endpoint=settings.azure_endpoint,
                           api_version=settings.azure_api_version,
                           timeout=25,max_retries=0)
    return OpenAI(api_key=settings.openai_api_key.get_secret_value(),timeout=25,max_retries=0)


def response_options(settings: Settings):
    if settings.assistant_mode == 'azure' and settings.azure_reasoning_effort:
        return {'reasoning': {'effort':settings.azure_reasoning_effort}}
    return {}
