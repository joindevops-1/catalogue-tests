import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SELENIUM_HUB = os.getenv('SELENIUM_HUB', 'http://localhost:4444')
APP_URL = os.getenv('APP_URL', 'http://web.daws88s.online')
CATALOGUE_URL = os.getenv('CATALOGUE_URL', 'http://catalogue.daws88s.online:8080')


@pytest.fixture(scope='session')
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    d = webdriver.Remote(command_executor=SELENIUM_HUB, options=options)
    d.implicitly_wait(10)
    yield d
    d.quit()


@pytest.fixture(scope='session')
def base_url():
    return APP_URL


@pytest.fixture(scope='session')
def catalogue_api_url():
    return CATALOGUE_URL
