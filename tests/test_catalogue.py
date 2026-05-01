import requests


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
