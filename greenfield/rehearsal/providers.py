"""Choose the model client without changing HR business functions."""
import os


def make_client():
    engine = os.environ.get('HR_AGENT_ENGINE', 'openai')
    if not os.environ.get('HR_AGENT_MODEL'):
        raise ValueError('Configure a model with the workshop launcher.')
    if engine == 'claude':
        from anthropic import Anthropic
        return Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'], timeout=45, max_retries=0)
    if engine == 'openai':
        from openai import OpenAI
        return OpenAI(api_key=os.environ['OPENAI_API_KEY'],
                      base_url=os.environ.get('OPENAI_BASE_URL') or None,
                      timeout=45, max_retries=0)
    raise ValueError('Choose claude or openai engine.')
