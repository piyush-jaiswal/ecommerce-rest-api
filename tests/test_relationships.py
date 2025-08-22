import pytest

from app.models import Category, Subcategory, Product


class TestRelationships:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        with client.application.app_context():
            assert Category.query.count() == 0
            assert Subcategory.query.count() == 0
            assert Product.query.count() == 0

    def _category_subcategory_ids(self, category_id):
        with self.client.application.app_context():
            category = Category.query.get(category_id)
            assert category is not None
            return sorted([subcategory.id for subcategory in category.subcategories])

    def _subcategory_category_ids(self, subcategory_id):
        with self.client.application.app_context():
            subcategory = Subcategory.query.get(subcategory_id)
            assert subcategory is not None
            return sorted([category.id for category in subcategory.categories])

    def _subcategory_product_ids(self, subcategory_id):
        with self.client.application.app_context():
            subcategory = Subcategory.query.get(subcategory_id)
            assert subcategory is not None
            return sorted([product.id for product in subcategory.products])

    def _product_subcategory_ids(self, product_id):
        with self.client.application.app_context():
            product = Product.query.get(product_id)
            assert product is not None
            return sorted([subcategory.id for subcategory in product.subcategories])

    def _category_product_ids_via_subcategories(self, category_id):
        with self.client.application.app_context():
            category = Category.query.get(category_id)
            assert category is not None
            return sorted({product.id for subcategory in category.subcategories for product in subcategory.products.all()})

    def test_create_category_with_subcategories(self, create_category, create_subcategory):
        subcategory1 = create_subcategory("SC_A").get_json()
        subcategory2 = create_subcategory("SC_B").get_json()
        response = create_category("Cat_AB", subcategories=[subcategory1["id"], subcategory2["id"]])
        assert response.status_code == 201
        category = response.get_json()

        assert self._category_subcategory_ids(category["id"]) == sorted([subcategory1["id"], subcategory2["id"]])
        assert category["id"] in self._subcategory_category_ids(subcategory1["id"])
        assert category["id"] in self._subcategory_category_ids(subcategory2["id"])

    def test_create_subcategory_with_categories_and_products(self, create_subcategory, create_category, create_product):
        category1 = create_category("C1").get_json()
        category2 = create_category("C2").get_json()
        product1 = create_product("P1", "des").get_json()
        product2 = create_product("P2", "desc").get_json()

        response = create_subcategory("SC_C1C2_P1P2", categories=[category1["id"], category2["id"]], products=[product1["id"], product2["id"]])
        assert response.status_code == 201
        subcategory = response.get_json()

        assert self._subcategory_category_ids(subcategory["id"]) == sorted([category1["id"], category2["id"]])
        assert self._subcategory_product_ids(subcategory["id"]) == sorted([product1["id"], product2["id"]])

    def test_create_product_with_subcategories_links_to_category_products(self, create_category, create_subcategory, create_product):
        category = create_category("C").get_json()
        subcategory = create_subcategory("SC", categories=[category["id"]]).get_json()
        response = create_product("P", "desc", subcategories=[subcategory["id"]])
        assert response.status_code == 201
        product = response.get_json()

        assert subcategory["id"] in self._product_subcategory_ids(product["id"])
        assert product["id"] in self._category_product_ids_via_subcategories(category["id"])
        assert product["id"] in self._subcategory_product_ids(subcategory["id"])

    def test_update_category_adds_subcategories(self, create_authenticated_headers, create_category, create_subcategory):
        subcategory1 = create_subcategory("U_SC1").get_json()
        subcategory2 = create_subcategory("U_SC2").get_json()
        category = create_category("U_Cat", subcategories=[subcategory1["id"]]).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(f"/category/{category['id']}/update", json={"subcategories": [subcategory2["id"]]}, headers=headers)
        assert update_response.status_code == 201

        assert self._category_subcategory_ids(category["id"]) == sorted([subcategory1["id"], subcategory2["id"]])

    def test_update_subcategory_adds_categories_and_products(self, create_authenticated_headers, create_category, create_product, create_subcategory):
        category1 = create_category("UC1").get_json()
        category2 = create_category("UC2").get_json()
        product1 = create_product("UP1").get_json()
        product2 = create_product("UP2").get_json()
        subcategory = create_subcategory("U_SC").get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/subcategory/{subcategory['id']}/update",
            json={"categories": [category1["id"], category2["id"]], "products": [product1["id"], product2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 201

        assert self._subcategory_category_ids(subcategory["id"]) == sorted([category1["id"], category2["id"]])
        assert self._subcategory_product_ids(subcategory["id"]) == sorted([product1["id"], product2["id"]])

    def test_update_product_adds_subcategories(self, create_authenticated_headers, create_product, create_subcategory):
        subcategory1 = create_subcategory("UPS1").get_json()
        subcategory2 = create_subcategory("UPS2").get_json()
        product = create_product("UP", "desc", subcategories=[subcategory1["id"]]).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(f"/product/{product['id']}/update", json={"subcategories": [subcategory2["id"]]}, headers=headers)
        assert update_response.status_code == 201

        assert self._product_subcategory_ids(product["id"]) == sorted([subcategory1["id"], subcategory2["id"]])

    def test_get_category_subcategories_empty(self, create_category):
        category = create_category("Cat_NoSC").get_json()
        resp = self.client.get(f"/category/{category['id']}/subcategories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "subcategories" in data
        assert data["subcategories"] == []

    def test_get_category_subcategories_populated(self, create_category, create_subcategory):
        subcategory1 = create_subcategory("SC1").get_json()
        subcategory2 = create_subcategory("SC2").get_json()
        category = create_category("Cat_WithSC", subcategories=[subcategory1["id"], subcategory2["id"]]).get_json()

        resp = self.client.get(f"/category/{category['id']}/subcategories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "subcategories" in data
        returned_ids = sorted([sc["id"] for sc in data["subcategories"]])
        assert returned_ids == sorted([subcategory1["id"], subcategory2["id"]])

    def test_get_category_products_empty(self, create_category):
        category = create_category("Cat_NoProd").get_json()
        resp = self.client.get(f"/category/{category['id']}/products")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "products" in data
        assert data["products"] == []

    def test_get_category_products_populated_with_pagination(self, create_category, create_subcategory, create_product):
        category = create_category("Cat_Prod").get_json()
        subcategory = create_subcategory("SC_Prod", categories=[category["id"]]).get_json()

        product_ids = set()
        for index in range(12):
            product_resp = create_product(f"P{index}", "desc", subcategories=[subcategory["id"]])
            product_ids.add(product_resp.get_json().get("id"))

        page1 = self.client.get(f"/category/{category['id']}/products?page=1").get_json()
        page2 = self.client.get(f"/category/{category['id']}/products?page=2").get_json()
        assert len(page1["products"]) == 10
        assert len(page2["products"]) == 2

        returned_product_ids = set(p["id"] for p in page1["products"] + page2["products"])
        assert returned_product_ids == product_ids

    def test_get_subcategory_categories_empty(self, create_subcategory):
        subcategory = create_subcategory("SC_NoCat").get_json()
        resp = self.client.get(f"/subcategory/{subcategory['id']}/categories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "categories" in data
        assert data["categories"] == []

    def test_get_subcategory_categories_populated(self, create_category, create_subcategory):
        category1 = create_category("C1").get_json()
        category2 = create_category("C2").get_json()
        subcategory = create_subcategory("SC_Cats", categories=[category1["id"], category2["id"]]).get_json()

        resp = self.client.get(f"/subcategory/{subcategory['id']}/categories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "categories" in data
        returned_ids = sorted([cat["id"] for cat in data["categories"]])
        assert returned_ids == sorted([category1["id"], category2["id"]])

    def test_get_subcategory_products_empty(self, create_subcategory):
        subcategory = create_subcategory("SC_NoProd").get_json()
        resp = self.client.get(f"/subcategory/{subcategory['id']}/products")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "products" in data
        assert data["products"] == []

    def test_get_subcategory_products_populated_with_pagination(self, create_subcategory, create_product):
        subcategory = create_subcategory("SC_Pag").get_json()

        product_ids = set()
        for index in range(11):
            product_resp = create_product(f"SP{index}", "desc", subcategories=[subcategory["id"]])
            product_ids.add(product_resp.get_json().get("id"))

        page1 = self.client.get(f"/subcategory/{subcategory['id']}/products?page=1").get_json()
        page2 = self.client.get(f"/subcategory/{subcategory['id']}/products?page=2").get_json()
        assert len(page1["products"]) == 10
        assert len(page2["products"]) == 1

        returned_product_ids = set(p["id"] for p in page1["products"] + page2["products"])
        assert returned_product_ids == product_ids

    def test_get_product_subcategories_empty(self, create_product):
        product = create_product("Prod_NoSC", "desc").get_json()
        resp = self.client.get(f"/product/{product['id']}/subcategories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "subcategories" in data
        assert data["subcategories"] == []

    def test_get_product_subcategories_populated(self, create_product, create_subcategory):
        subcategory1 = create_subcategory("S1").get_json()
        subcategory2 = create_subcategory("S2").get_json()
        product = create_product("Prod_SC", "desc", subcategories=[subcategory1["id"], subcategory2["id"]]).get_json()

        resp = self.client.get(f"/product/{product['id']}/subcategories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "subcategories" in data
        returned_ids = sorted([sc["id"] for sc in data["subcategories"]])
        assert returned_ids == sorted([subcategory1["id"], subcategory2["id"]])

    @pytest.mark.parametrize(
        "path",
        [
            "/category/999999/subcategories",
            "/category/999999/products",
            "/subcategory/999999/categories",
            "/subcategory/999999/products",
            "/product/999999/subcategories",
        ],
    )
    def test_relationship_getters_404(self, path):
        resp = self.client.get(path)
        assert resp.status_code == 404
