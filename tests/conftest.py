import random

import pytest


@pytest.fixture(autouse=True)
def _seed_rng():
    """Deixa os testes do AG reproduzíveis."""
    random.seed(0)
    yield
    random.seed()
