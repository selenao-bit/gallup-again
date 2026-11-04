"""Provider routing and configuration without network requests or private settings."""
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from app.config import Settings
from app.ai import provider
from app.services.access import DemoError

URL='postgresql://test:test@localhost/test'
AZURE=dict(database_url=URL,assistant_mode='azure',azure_openai_key='azure-test-only',
           azure_endpoint='https://test-resource.openai.azure.com/',azure_deployment='test-deployment')


def test_azure_key_is_only_given_to_azure_client(monkeypatch):
    azure=Mock();direct=Mock()
    monkeypatch.setattr(provider,'AzureOpenAI',azure)
    monkeypatch.setattr(provider,'OpenAI',direct)
    settings=Settings(**AZURE,openai_api_key='direct-test-only')
    provider.create_client(settings)
    direct.assert_not_called()
    assert azure.call_args.kwargs==dict(api_key='azure-test-only',azure_endpoint=AZURE['azure_endpoint'],
                                      api_version='2025-03-01-preview',timeout=25,max_retries=0)
    assert settings.assistant_model=='test-deployment'


@pytest.mark.parametrize('missing',['azure_openai_key','azure_endpoint','azure_deployment'])
def test_incomplete_azure_never_falls_back_to_direct(monkeypatch,missing):
    azure=Mock();direct=Mock()
    monkeypatch.setattr(provider,'AzureOpenAI',azure)
    monkeypatch.setattr(provider,'OpenAI',direct)
    values={**AZURE,missing:None,'openai_api_key':'direct-test-only'}
    with pytest.raises(DemoError) as error:provider.create_client(Settings(**values))
    assert error.value.code=='assistant_unavailable'
    azure.assert_not_called();direct.assert_not_called()


def test_azure_aliases_preserve_process_precedence(root_env_path):
    root_env_path.write_text('DATABASE_URL='+URL+'\nGW_AZURE_RESOURCE=test-resource\nGW_AZURE_OPENAI_KEY=file-test-only\nGW_AZURE_MODEL=file-deployment\n')
    settings=Settings.from_environment({'ASSISTANT_MODE':'azure','AZURE_OPENAI_API_KEY':'env-test-only','AZURE_OPENAI_DEPLOYMENT':'env-deployment'})
    assert settings.azure_openai_key.get_secret_value()=='env-test-only'
    assert settings.azure_endpoint==AZURE['azure_endpoint']
    assert settings.assistant_model=='env-deployment' and settings.assistant_available
    assert 'env-test-only' not in settings.model_dump_json()


@pytest.mark.parametrize('endpoint',['http://test-resource.openai.azure.com/','https://example.com/','https://test-resource.openai.azure.com/openai/v1/','https://test-resource.openai.azure.com/?api-key=test-only'])
def test_azure_rejects_non_resource_endpoints(endpoint):
    with pytest.raises(ValidationError):Settings(**{**AZURE,'azure_endpoint':endpoint})


@pytest.mark.parametrize('effort',['none','low','medium','high'])
def test_reasoning_options_are_explicit_and_azure_only(effort):
    settings=Settings(**AZURE,azure_reasoning_effort=effort)
    assert provider.response_options(settings)=={'reasoning':{'effort':effort}}
    direct=Settings(database_url=URL,assistant_mode='openai',openai_api_key='test-only',azure_reasoning_effort=effort)
    assert provider.response_options(direct)=={}


def test_fast_reasoning_setting_loads_from_environment(root_env_path):
    root_env_path.write_text('DATABASE_URL='+URL+'\nAZURE_OPENAI_REASONING_EFFORT=none\n')
    assert Settings.from_environment({}).azure_reasoning_effort=='none'
