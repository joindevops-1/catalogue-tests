import os
import pytest

CATALOGUE_URL = os.getenv('CATALOGUE_URL', 'http://catalogue.daws88s.online:8080')


@pytest.fixture(scope='session')
def catalogue_api_url():
    return CATALOGUE_URL
