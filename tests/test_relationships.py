import pytest

from app.models import Category, Product, Subcategory


class TestRelationships:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        assert Category.query.count() == 0
        assert Subcategory.query.count() == 0
        assert Product.query.count() == 0

    def _category_subcategory_ids(self, category_id):
        category = Category.query.get(category_id)
        assert category is not None
        return sorted([subcategory.id for subcategory in category.subcategories])

    def _subcategory_category_ids(self, subcategory_id):
        subcategory = Subcategory.query.get(subcategory_id)
        assert subcategory is not None
        return sorted([category.id for category in subcategory.categories])

    def _subcategory_product_ids(self, subcategory_id):
        subcategory = Subcategory.query.get(subcategory_id)
        assert subcategory is not None
        return sorted([product.id for product in subcategory.products])

    def _product_subcategory_ids(self, product_id):
        product = Product.query.get(product_id)
        assert product is not None
        return sorted([subcategory.id for subcategory in product.subcategories])

    def _category_product_ids_via_subcategories(self, category_id):
        category = Category.query.get(category_id)
        assert category is not None
        return sorted(
            {
                product.id
                for subcategory in category.subcategories
                for product in subcategory.products.all()
            }
        )

    def _assert_related_collection(self, resp, key, expected_ids=None, status_code=200):
        assert resp.status_code == status_code
        data = resp.get_json()
        assert key in data
        returned_ids = sorted([item["id"] for item in data[key]])
        expected_ids = expected_ids or []
        assert returned_ids == sorted(expected_ids)

    def test_create_category_with_subcategories(
        self, create_category, create_subcategory
    ):
        subcategory1 = create_subcategory("SC_A").get_json()
        subcategory2 = create_subcategory("SC_B").get_json()
        response = create_category(
            "Cat_AB", subcategories=[subcategory1["id"], subcategory2["id"]]
        )
        assert response.status_code == 201
        category = response.get_json()

        assert self._category_subcategory_ids(category["id"]) == sorted(
            [subcategory1["id"], subcategory2["id"]]
        )
        assert category["id"] in self._subcategory_category_ids(subcategory1["id"])
        assert category["id"] in self._subcategory_category_ids(subcategory2["id"])

    def test_create_subcategory_with_categories_and_products(
        self, create_subcategory, create_category, create_product
    ):
        category1 = create_category("C1").get_json()
        category2 = create_category("C2").get_json()
        product1 = create_product("P1", "des").get_json()
        product2 = create_product("P2", "desc").get_json()

        response = create_subcategory(
            "SC_C1C2_P1P2",
            categories=[category1["id"], category2["id"]],
            products=[product1["id"], product2["id"]],
        )
        assert response.status_code == 201
        subcategory = response.get_json()

        assert self._subcategory_category_ids(subcategory["id"]) == sorted(
            [category1["id"], category2["id"]]
        )
        assert self._subcategory_product_ids(subcategory["id"]) == sorted(
            [product1["id"], product2["id"]]
        )

    def test_create_product_with_subcategories_links_to_category_products(
        self, create_category, create_subcategory, create_product
    ):
        category = create_category("C").get_json()
        subcategory = create_subcategory("SC", categories=[category["id"]]).get_json()
        response = create_product("P", "desc", subcategories=[subcategory["id"]])
        assert response.status_code == 201
        product = response.get_json()

        assert subcategory["id"] in self._product_subcategory_ids(product["id"])
        assert product["id"] in self._category_product_ids_via_subcategories(
            category["id"]
        )
        assert product["id"] in self._subcategory_product_ids(subcategory["id"])

    def test_update_category_replaces_subcategories(
        self, create_authenticated_headers, create_category, create_subcategory
    ):
        subcategory1 = create_subcategory("U_SC1").get_json()
        subcategory2 = create_subcategory("U_SC2").get_json()
        category = create_category(
            "U_Cat", subcategories=[subcategory1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/categories/{category['id']}",
            json={"subcategories": [subcategory2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._category_subcategory_ids(category["id"]) == [subcategory2["id"]]

    def test_update_category_clears_subcategories(
        self, create_authenticated_headers, create_category, create_subcategory
    ):
        subcategory = create_subcategory("C_SC").get_json()
        category = create_category(
            "C_Cat", subcategories=[subcategory["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/categories/{category['id']}",
            json={"subcategories": []},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert self._category_subcategory_ids(category["id"]) == []

    def test_patch_category_add_subcategories(
        self, create_authenticated_headers, create_category, create_subcategory
    ):
        subcategory1 = create_subcategory("PA_SC1").get_json()
        subcategory2 = create_subcategory("PA_SC2").get_json()
        category = create_category(
            "PA_Cat", subcategories=[subcategory1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/categories/{category['id']}",
            json={"subcategories_add": [subcategory2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._category_subcategory_ids(category["id"]) == sorted(
            [subcategory1["id"], subcategory2["id"]]
        )

    def test_patch_category_remove_subcategories(
        self, create_authenticated_headers, create_category, create_subcategory
    ):
        subcategory1 = create_subcategory("PR_SC1").get_json()
        subcategory2 = create_subcategory("PR_SC2").get_json()
        category = create_category(
            "PR_Cat", subcategories=[subcategory1["id"], subcategory2["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/categories/{category['id']}",
            json={"subcategories_remove": [subcategory1["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._category_subcategory_ids(category["id"]) == [subcategory2["id"]]

    def test_patch_category_add_and_remove_subcategories(
        self, create_authenticated_headers, create_category, create_subcategory
    ):
        subcategory1 = create_subcategory("PAR_SC1").get_json()
        subcategory2 = create_subcategory("PAR_SC2").get_json()
        subcategory3 = create_subcategory("PAR_SC3").get_json()
        category = create_category(
            "PAR_Cat",
            subcategories=[subcategory1["id"], subcategory2["id"]],
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/categories/{category['id']}",
            json={
                "subcategories_add": [subcategory3["id"]],
                "subcategories_remove": [subcategory1["id"]],
            },
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._category_subcategory_ids(category["id"]) == sorted(
            [subcategory2["id"], subcategory3["id"]]
        )

    def test_patch_category_add_linked_subcategory_is_noop(
        self, create_authenticated_headers, create_category, create_subcategory
    ):
        subcategory = create_subcategory("PL_SC").get_json()
        category = create_category(
            "PL_Cat", subcategories=[subcategory["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/categories/{category['id']}",
            json={"subcategories_add": [subcategory["id"]]},
            headers=headers,
        )

        assert response.status_code == 200
        assert self._category_subcategory_ids(category["id"]) == [subcategory["id"]]

    def test_patch_category_add_remove_overlap_returns_422(
        self, create_authenticated_headers, create_category
    ):
        category = create_category("Overlap_Cat").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/categories/{category['id']}",
            json={"subcategories_add": [1, 2], "subcategories_remove": [2, 3]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "2" in data["message"]

    def test_patch_category_invalid_subcategory(
        self, create_authenticated_headers, create_category
    ):
        category = create_category("INV_Cat").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/categories/{category['id']}",
            json={"subcategories_add": [999999]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "One or more subcategories not present" in data["message"]
        assert self._category_subcategory_ids(category["id"]) == []

    def test_patch_category_noop(self, create_authenticated_headers, create_category):
        category = create_category("NOOP_Cat").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/categories/{category['id']}",
            json={},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.get_json()["name"] == "NOOP_Cat"

    def test_update_subcategory_replaces_categories_and_products(
        self,
        create_authenticated_headers,
        create_category,
        create_product,
        create_subcategory,
    ):
        category1 = create_category("USC_C1").get_json()
        category2 = create_category("USC_C2").get_json()
        product1 = create_product("USC_P1").get_json()
        product2 = create_product("USC_P2").get_json()
        subcategory = create_subcategory(
            "USC_SC", categories=[category1["id"]], products=[product1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/subcategories/{subcategory['id']}",
            json={
                "categories": [category2["id"]],
                "products": [product2["id"]],
            },
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_category_ids(subcategory["id"]) == [category2["id"]]
        assert self._subcategory_product_ids(subcategory["id"]) == [product2["id"]]

    def test_update_subcategory_clears_categories(
        self,
        create_authenticated_headers,
        create_category,
        create_subcategory,
    ):
        category = create_category("USC_CC").get_json()
        subcategory = create_subcategory(
            "USC_CS", categories=[category["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/subcategories/{subcategory['id']}",
            json={"categories": []},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert self._subcategory_category_ids(subcategory["id"]) == []

    def test_update_subcategory_clears_products(
        self,
        create_authenticated_headers,
        create_product,
        create_subcategory,
    ):
        product = create_product("USC_CP").get_json()
        subcategory = create_subcategory("USC_PS", products=[product["id"]]).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/subcategories/{subcategory['id']}",
            json={"products": []},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert self._subcategory_product_ids(subcategory["id"]) == []

    def test_patch_subcategory_add_categories(
        self,
        create_authenticated_headers,
        create_category,
        create_subcategory,
    ):
        category1 = create_category("PSAC_C1").get_json()
        category2 = create_category("PSAC_C2").get_json()
        subcategory = create_subcategory(
            "PSAC_SC", categories=[category1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"categories_add": [category2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_category_ids(subcategory["id"]) == sorted(
            [category1["id"], category2["id"]]
        )

    def test_patch_subcategory_remove_categories(
        self,
        create_authenticated_headers,
        create_category,
        create_subcategory,
    ):
        category1 = create_category("PSRC_C1").get_json()
        category2 = create_category("PSRC_C2").get_json()
        subcategory = create_subcategory(
            "PSRC_SC", categories=[category1["id"], category2["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"categories_remove": [category1["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_category_ids(subcategory["id"]) == [category2["id"]]

    def test_patch_subcategory_add_and_remove_categories(
        self,
        create_authenticated_headers,
        create_category,
        create_subcategory,
    ):
        category1 = create_category("PSARC_C1").get_json()
        category2 = create_category("PSARC_C2").get_json()
        category3 = create_category("PSARC_C3").get_json()
        subcategory = create_subcategory(
            "PSARC_SC",
            categories=[category1["id"], category2["id"]],
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={
                "categories_add": [category3["id"]],
                "categories_remove": [category1["id"]],
            },
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_category_ids(subcategory["id"]) == sorted(
            [category2["id"], category3["id"]]
        )

    def test_patch_subcategory_add_linked_category_is_noop(
        self,
        create_authenticated_headers,
        create_category,
        create_subcategory,
    ):
        category = create_category("PSALC_C").get_json()
        subcategory = create_subcategory(
            "PSALC_SC", categories=[category["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"categories_add": [category["id"]]},
            headers=headers,
        )

        assert response.status_code == 200
        assert self._subcategory_category_ids(subcategory["id"]) == [category["id"]]

    def test_patch_subcategory_add_remove_category_overlap_returns_422(
        self,
        create_authenticated_headers,
        create_category,
        create_subcategory,
    ):
        category = create_category("PSAROC_C").get_json()
        subcategory = create_subcategory("PSAROC_SC").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={
                "categories_add": [category["id"]],
                "categories_remove": [category["id"]],
            },
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert str(category["id"]) in data["message"]

    def test_patch_subcategory_add_products(
        self,
        create_authenticated_headers,
        create_product,
        create_subcategory,
    ):
        product1 = create_product("PSAP_P1").get_json()
        product2 = create_product("PSAP_P2").get_json()
        subcategory = create_subcategory(
            "PSAP_SC", products=[product1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"products_add": [product2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_product_ids(subcategory["id"]) == sorted(
            [product1["id"], product2["id"]]
        )

    def test_patch_subcategory_remove_products(
        self,
        create_authenticated_headers,
        create_product,
        create_subcategory,
    ):
        product1 = create_product("PSRP_P1").get_json()
        product2 = create_product("PSRP_P2").get_json()
        subcategory = create_subcategory(
            "PSRP_SC", products=[product1["id"], product2["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"products_remove": [product1["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_product_ids(subcategory["id"]) == [product2["id"]]

    def test_patch_subcategory_add_and_remove_products(
        self,
        create_authenticated_headers,
        create_product,
        create_subcategory,
    ):
        product1 = create_product("PSARP_P1").get_json()
        product2 = create_product("PSARP_P2").get_json()
        product3 = create_product("PSARP_P3").get_json()
        subcategory = create_subcategory(
            "PSARP_SC",
            products=[product1["id"], product2["id"]],
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={
                "products_add": [product3["id"]],
                "products_remove": [product1["id"]],
            },
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_product_ids(subcategory["id"]) == sorted(
            [product2["id"], product3["id"]]
        )

    def test_patch_subcategory_add_linked_product_is_noop(
        self,
        create_authenticated_headers,
        create_product,
        create_subcategory,
    ):
        product = create_product("PSALP_P").get_json()
        subcategory = create_subcategory(
            "PSALP_SC", products=[product["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"products_add": [product["id"]]},
            headers=headers,
        )

        assert response.status_code == 200
        assert self._subcategory_product_ids(subcategory["id"]) == [product["id"]]

    def test_patch_subcategory_add_remove_product_overlap_returns_422(
        self,
        create_authenticated_headers,
        create_product,
        create_subcategory,
    ):
        product = create_product("PSAROP_P").get_json()
        subcategory = create_subcategory("PSAROP_SC").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"products_add": [product["id"]], "products_remove": [product["id"]]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert str(product["id"]) in data["message"]

    def test_patch_subcategory_invalid_category(
        self,
        create_authenticated_headers,
        create_subcategory,
    ):
        subcategory = create_subcategory("PSIC_SC").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"categories_add": [999999]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "One or more categories not present" in data["message"]
        assert self._subcategory_category_ids(subcategory["id"]) == []

    def test_patch_subcategory_invalid_product(
        self,
        create_authenticated_headers,
        create_subcategory,
    ):
        subcategory = create_subcategory("PSIP_SC").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={"products_add": [999999]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "One or more products not present" in data["message"]
        assert self._subcategory_product_ids(subcategory["id"]) == []

    def test_patch_subcategory_noop(
        self,
        create_authenticated_headers,
        create_subcategory,
    ):
        subcategory = create_subcategory("PSN_SC").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/subcategories/{subcategory['id']}",
            json={},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.get_json()["name"] == "PSN_SC"

    def test_update_product_replaces_subcategories(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory1 = create_subcategory("UPS1").get_json()
        subcategory2 = create_subcategory("UPS2").get_json()
        product = create_product(
            "UP", "desc", subcategories=[subcategory1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/products/{product['id']}",
            json={"subcategories": [subcategory2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._product_subcategory_ids(product["id"]) == [subcategory2["id"]]

    def test_update_product_clears_subcategories(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory = create_subcategory("UPC_SC").get_json()
        product = create_product(
            "UPC", "desc", subcategories=[subcategory["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/products/{product['id']}",
            json={"subcategories": []},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert self._product_subcategory_ids(product["id"]) == []

    def test_patch_product_add_subcategories(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory1 = create_subcategory("PPA_SC1").get_json()
        subcategory2 = create_subcategory("PPA_SC2").get_json()
        product = create_product(
            "PPA", "desc", subcategories=[subcategory1["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/products/{product['id']}",
            json={"subcategories_add": [subcategory2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._product_subcategory_ids(product["id"]) == sorted(
            [subcategory1["id"], subcategory2["id"]]
        )

    def test_patch_product_remove_subcategories(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory1 = create_subcategory("PPR_SC1").get_json()
        subcategory2 = create_subcategory("PPR_SC2").get_json()
        product = create_product(
            "PPR",
            "desc",
            subcategories=[subcategory1["id"], subcategory2["id"]],
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/products/{product['id']}",
            json={"subcategories_remove": [subcategory1["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._product_subcategory_ids(product["id"]) == [subcategory2["id"]]

    def test_patch_product_add_and_remove_subcategories(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory1 = create_subcategory("PPAR_SC1").get_json()
        subcategory2 = create_subcategory("PPAR_SC2").get_json()
        subcategory3 = create_subcategory("PPAR_SC3").get_json()
        product = create_product(
            "PPAR",
            "desc",
            subcategories=[subcategory1["id"], subcategory2["id"]],
        ).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.patch(
            f"/products/{product['id']}",
            json={
                "subcategories_add": [subcategory3["id"]],
                "subcategories_remove": [subcategory1["id"]],
            },
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._product_subcategory_ids(product["id"]) == sorted(
            [subcategory2["id"], subcategory3["id"]]
        )

    def test_patch_product_add_linked_subcategory_is_noop(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory = create_subcategory("PPL_SC").get_json()
        product = create_product(
            "PPL", "desc", subcategories=[subcategory["id"]]
        ).get_json()

        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/products/{product['id']}",
            json={"subcategories_add": [subcategory["id"]]},
            headers=headers,
        )

        assert response.status_code == 200
        assert self._product_subcategory_ids(product["id"]) == [subcategory["id"]]

    def test_patch_product_add_remove_overlap_returns_422(
        self, create_authenticated_headers, create_product
    ):
        product = create_product("PPO", "desc").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/products/{product['id']}",
            json={"subcategories_add": [1, 2], "subcategories_remove": [2, 3]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "2" in data["message"]

    def test_patch_product_invalid_subcategory(
        self, create_authenticated_headers, create_product
    ):
        product = create_product("PPIS", "desc").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/products/{product['id']}",
            json={"subcategories_add": [999999]},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "One or more subcategories not present" in data["message"]
        assert self._product_subcategory_ids(product["id"]) == []

    def test_patch_product_noop(self, create_authenticated_headers, create_product):
        product = create_product("PPN", "desc").get_json()
        headers = create_authenticated_headers()
        response = self.client.patch(
            f"/products/{product['id']}",
            json={},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "PPN"
        assert data["description"] == "desc"

    def test_get_category_subcategories_empty(self, create_category):
        category = create_category("Cat_NoSC").get_json()
        resp = self.client.get(f"/categories/{category['id']}/subcategories")
        self._assert_related_collection(resp, "subcategories")

    def test_get_category_subcategories_populated(
        self, create_category, create_subcategory
    ):
        subcategory1 = create_subcategory("SC1").get_json()
        subcategory2 = create_subcategory("SC2").get_json()
        category = create_category(
            "Cat_WithSC", subcategories=[subcategory1["id"], subcategory2["id"]]
        ).get_json()

        resp = self.client.get(f"/categories/{category['id']}/subcategories")
        self._assert_related_collection(
            resp, "subcategories", expected_ids=[subcategory1["id"], subcategory2["id"]]
        )

    def test_get_category_products_empty(self, create_category):
        category = create_category("Cat_NoProd").get_json()
        resp = self.client.get(f"/categories/{category['id']}/products")
        self._assert_related_collection(resp, "products")

    def test_get_category_products_populated_with_pagination(
        self, create_category, create_subcategory, create_product
    ):
        category = create_category("Cat_Prod").get_json()
        subcategory = create_subcategory(
            "SC_Prod", categories=[category["id"]]
        ).get_json()

        product_ids = set()
        for index in range(12):
            product_resp = create_product(
                f"P{index}", "desc", subcategories=[subcategory["id"]]
            )
            product_ids.add(product_resp.get_json().get("id"))

        page1 = self.client.get(f"/categories/{category['id']}/products").get_json()
        assert page1["cursor"]["prev"] is None
        assert type(page1["cursor"]["next"]) is str

        next_cursor = page1["cursor"]["next"]
        page2 = self.client.get(
            f"/categories/{category['id']}/products?cursor={next_cursor}"
        ).get_json()
        assert page2["cursor"]["next"] is None
        assert isinstance(page2["cursor"]["prev"], str)
        assert len(page1["products"]) == 10
        assert len(page2["products"]) == 2

        returned_product_ids = set(
            p["id"] for p in page1["products"] + page2["products"]
        )
        assert returned_product_ids == product_ids

    def test_get_subcategory_categories_empty(self, create_subcategory):
        subcategory = create_subcategory("SC_NoCat").get_json()
        resp = self.client.get(f"/subcategories/{subcategory['id']}/categories")
        self._assert_related_collection(resp, "categories")

    def test_get_subcategory_categories_populated(
        self, create_category, create_subcategory
    ):
        category1 = create_category("C1").get_json()
        category2 = create_category("C2").get_json()
        subcategory = create_subcategory(
            "SC_Cats", categories=[category1["id"], category2["id"]]
        ).get_json()

        resp = self.client.get(f"/subcategories/{subcategory['id']}/categories")
        self._assert_related_collection(
            resp, "categories", expected_ids=[category1["id"], category2["id"]]
        )

    def test_get_subcategory_products_empty(self, create_subcategory):
        subcategory = create_subcategory("SC_NoProd").get_json()
        resp = self.client.get(f"/subcategories/{subcategory['id']}/products")
        self._assert_related_collection(resp, "products")

    def test_get_subcategory_products_populated_with_pagination(
        self, create_subcategory, create_product
    ):
        subcategory = create_subcategory("SC_Pag").get_json()

        product_ids = set()
        for index in range(11):
            product_resp = create_product(
                f"SP{index}", "desc", subcategories=[subcategory["id"]]
            )
            product_ids.add(product_resp.get_json().get("id"))

        page1 = self.client.get(
            f"/subcategories/{subcategory['id']}/products"
        ).get_json()
        assert page1["cursor"]["prev"] is None
        assert type(page1["cursor"]["next"]) is str

        next_cursor = page1["cursor"]["next"]
        page2 = self.client.get(
            f"/subcategories/{subcategory['id']}/products?cursor={next_cursor}"
        ).get_json()
        assert page2["cursor"]["next"] is None
        assert isinstance(page2["cursor"]["prev"], str)
        assert len(page1["products"]) == 10
        assert len(page2["products"]) == 1

        returned_product_ids = set(
            p["id"] for p in page1["products"] + page2["products"]
        )
        assert returned_product_ids == product_ids

    def test_get_product_subcategories_empty(self, create_product):
        product = create_product("Prod_NoSC", "desc").get_json()
        resp = self.client.get(f"/products/{product['id']}/subcategories")
        self._assert_related_collection(resp, "subcategories")

    def test_get_product_subcategories_populated(
        self, create_product, create_subcategory
    ):
        subcategory1 = create_subcategory("S1").get_json()
        subcategory2 = create_subcategory("S2").get_json()
        product = create_product(
            "Prod_SC", "desc", subcategories=[subcategory1["id"], subcategory2["id"]]
        ).get_json()

        resp = self.client.get(f"/products/{product['id']}/subcategories")
        self._assert_related_collection(
            resp, "subcategories", expected_ids=[subcategory1["id"], subcategory2["id"]]
        )

    @pytest.mark.parametrize(
        "path",
        [
            "/categories/999999/subcategories",
            "/categories/999999/products",
            "/subcategories/999999/categories",
            "/subcategories/999999/products",
            "/products/999999/subcategories",
        ],
    )
    def test_relationship_getters_404(self, path):
        resp = self.client.get(path)
        assert resp.status_code == 404
