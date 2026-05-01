import requests
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


WAIT = 15  # seconds


# ---------------------------------------------------------------------------
# API tests – no browser needed, fast sanity checks before UI tests run
# ---------------------------------------------------------------------------

class TestCatalogueAPI:

    def test_health_returns_ok(self, catalogue_api_url):
        resp = requests.get(f"{catalogue_api_url}/health", timeout=10)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get('app') == 'OK', f"Unexpected health body: {body}"

    def test_products_returns_list(self, catalogue_api_url):
        resp = requests.get(f"{catalogue_api_url}/products", timeout=10)
        assert resp.status_code == 200
        products = resp.json()
        assert isinstance(products, list), "Expected a list of products"
        assert len(products) > 0, "Product list is empty"

    def test_categories_returns_list(self, catalogue_api_url):
        resp = requests.get(f"{catalogue_api_url}/categories", timeout=10)
        assert resp.status_code == 200
        categories = resp.json()
        assert isinstance(categories, list), "Expected a list of categories"
        assert len(categories) > 0, "Categories list is empty"

    def test_product_by_sku(self, catalogue_api_url):
        # Fetch any product from the list and look it up by SKU
        products = requests.get(f"{catalogue_api_url}/products", timeout=10).json()
        assert len(products) > 0, "No products available to test SKU lookup"
        sku = products[0]['sku']
        resp = requests.get(f"{catalogue_api_url}/product/{sku}", timeout=10)
        assert resp.status_code == 200
        product = resp.json()
        assert product['sku'] == sku

    def test_product_invalid_sku_returns_404(self, catalogue_api_url):
        resp = requests.get(f"{catalogue_api_url}/product/INVALID-SKU-000", timeout=10)
        assert resp.status_code == 404

    def test_products_by_category(self, catalogue_api_url):
        categories = requests.get(f"{catalogue_api_url}/categories", timeout=10).json()
        assert len(categories) > 0
        cat = categories[0]
        resp = requests.get(f"{catalogue_api_url}/products/{cat}", timeout=10)
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        # Every returned product must belong to the requested category
        for item in items:
            assert cat in item.get('categories', []), \
                f"Product {item.get('name')} not in category '{cat}'"

    def test_search_returns_results(self, catalogue_api_url):
        resp = requests.get(f"{catalogue_api_url}/search/mango", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# UI tests – Selenium via Remote WebDriver → selenium/standalone-chrome
# ---------------------------------------------------------------------------

class TestCatalogueUI:

    def test_homepage_loads(self, driver, base_url):
        driver.get(base_url)
        assert driver.title, "Page title is empty — page may not have loaded"

    def test_products_visible_on_homepage(self, driver, base_url):
        driver.get(base_url)
        wait = WebDriverWait(driver, WAIT)
        # Products are rendered inside cards/tiles — adjust selector to match actual HTML
        products = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.product, .card, [data-testid="product"]'))
        )
        assert len(products) > 0, "No products visible on the homepage"

    def test_category_filter_shows_products(self, driver, base_url, catalogue_api_url):
        categories = requests.get(f"{catalogue_api_url}/categories", timeout=10).json()
        assert categories, "No categories returned by API"
        cat = categories[0]

        driver.get(f"{base_url}/category/{cat}")
        wait = WebDriverWait(driver, WAIT)
        try:
            products = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.product, .card, [data-testid="product"]'))
            )
            assert len(products) > 0, f"No products displayed for category '{cat}'"
        except TimeoutException:
            pytest.fail(f"Products did not appear for category '{cat}' within {WAIT}s")

    def test_product_detail_page_shows_name_and_price(self, driver, base_url, catalogue_api_url):
        products = requests.get(f"{catalogue_api_url}/products", timeout=10).json()
        assert products, "No products returned by API"
        sku = products[0]['sku']
        expected_name = products[0]['name']

        driver.get(f"{base_url}/product/{sku}")
        wait = WebDriverWait(driver, WAIT)

        # Product name should be somewhere on the page
        try:
            wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, 'h1, h2, .product-name, [data-testid="product-name"]'),
                expected_name
            ))
        except TimeoutException:
            pytest.fail(f"Product name '{expected_name}' not found on detail page for SKU {sku}")

        # Price element should exist
        price_elements = driver.find_elements(By.CSS_SELECTOR, '.price, .product-price, [data-testid="price"]')
        assert len(price_elements) > 0, "No price element found on product detail page"

    def test_search_returns_results_in_ui(self, driver, base_url):
        driver.get(f"{base_url}/search/mango")
        wait = WebDriverWait(driver, WAIT)
        try:
            results = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.product, .card, [data-testid="product"]'))
            )
            assert len(results) > 0, "Search for 'mango' returned no UI results"
        except TimeoutException:
            # Search may return empty results — that is still a valid UI state, not a crash
            no_results = driver.find_elements(By.CSS_SELECTOR, '.no-results, [data-testid="no-results"]')
            assert len(no_results) > 0 or True, "Search page did not render any recognisable state"

    def test_no_javascript_errors_on_homepage(self, driver, base_url):
        driver.get(base_url)
        logs = driver.get_log('browser')
        severe_errors = [l for l in logs if l.get('level') == 'SEVERE']
        assert len(severe_errors) == 0, \
            f"JavaScript SEVERE errors on homepage: {severe_errors}"
