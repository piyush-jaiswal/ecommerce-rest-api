from flask import request, abort, jsonify

from app import app, db
from app.models import Category, Subcategory, Product, category_subcategory, subcategory_product


@app.route('/category/create', methods=['POST'])
def create_category():
    """
    Create Category
    ---
    tags:
        - Category
    description: Create a new category.
    requestBody:
        required: true
        description: name - Name of the category <br> subcategories - Array of subcategory ids (optional)
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - name
                    properties:
                        name:
                            type: string
                        subcategories:
                            type: array
                            items:
                                type: integer
    responses:
        201:
            description: Category created successfully.
        400:
            description: Invalid input.
        500:
            description: Error occurred.
    """
    if not request.json:
        abort(400)

    try:
        category = Category(name=request.json.get('name'))
        sc_ids = request.json.get('subcategories')
        if sc_ids is not None:
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids))
            category.subcategories.extend(subcategories)
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_json()), 201
    except:
        return "Error occured", 500


@app.route('/category/<int:c_id>', methods=['GET'])
def get_category(c_id):
    """
    Get Category
    ---
    tags:
        - Category
    description: Get a category by ID.
    parameters:
        - in: path
          name: c_id
          required: true
          type: integer
          description: Category ID
    responses:
        200:
            description: Category retrieved successfully.
        404:
            description: Category not found.
    """
    category = Category.query.get(c_id)
    if category is None:
        abort(404)
    return jsonify(category.to_json()), 200


@app.route('/category/<int:c_id>/update', methods=['PUT'])
def update_category(c_id):
    """
    Update Category
    ---
    tags:
        - Category
    description: Update an existing category.
    parameters:
        - in: path
          name: c_id
          required: true
          type: integer
          description: Category ID
    requestBody:
        required: true
        description: name - Name of the category (optional) <br> subcategories - Array of subcategory ids
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        name:
                            type: string
                        subcategories:
                            type: array
                            items:
                                type: integer
    responses:
        201:
            description: Category updated successfully.
        400:
            description: Invalid input.
        404:
            description: Category not found.
        500:
            description: Error occurred.
    """
    if not request.json:
        abort(400)

    category = Category.query.get(c_id)
    if category is None:
        abort(404)
    try:
        name = request.json.get('name')
        sc_ids = request.json.get('subcategories')
        if name is not None:
            category.name = request.json.get('name')
        if sc_ids is not None:
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids))
            category.subcategories.extend(subcategories)
        db.session.commit()
        return jsonify(category.to_json()), 201
    except:
        return "Error occured", 500


@app.route("/category/<int:c_id>", methods=["DELETE"])
def delete_category(c_id):
    """
    Delete Category
    ---
    tags:
        - Category
    description: Delete a category by ID.
    parameters:
        - in: path
          name: c_id
          required: true
          type: integer
          description: Category ID
    responses:
        200:
            description: Category deleted successfully.
        404:
            description: Category not found.
        500:
            description: Error occurred.
    """
    category = Category.query.get(c_id)
    if category is None:
        abort(404)
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'result': True}), 200
    except:
        return "Error occured", 500


@app.route('/categories', methods=['GET'])
def get_all_categories():
    """
    Get All Categories
    ---
    tags:
        - Category
    description: Get all categories.
    responses:
        200:
            description: A list of categories.
    """
    categories = Category.query.order_by(Category.name).all()
    return jsonify({"categories": [category.to_json() for category in categories]}), 200


@app.route('/category/<int:c_id>/subcategories', methods=['GET'])
def get_category_subcategories(c_id):
    """
    Get Subcategories within a Category.
    ---
    tags:
        - Category
    description: Get Subcategories within a Category.
    parameters:
        - in: path
          name: c_id
          required: true
          type: integer
          description: Category ID
    responses:
        200:
            description: Subcategories retrieved successfully.
        404:
            description: Category not found.
        500:
            description: Error occurred.
    """
    category = Category.query.get(c_id)
    if category is None:
        abort(404)

    try:
        return {
            "subcategories": [sc.to_json() for sc in category.subcategories]
        }, 200
    except:
        return "Error occured", 500


@app.route('/category/<int:c_id>/products', methods=['GET'])
def get_category_products(c_id):
    """
    Get Products within a Category.
    ---
    tags:
        - Category
    description: Get Products for a Category.
    parameters:
        - in: path
          name: c_id
          required: true
          type: integer
          description: Category ID
        - in: query
          name: page
          type: integer
          default: 1
          description: Page number
    responses:
        200:
            description: Products retrieved successfully.
        404:
            description: Category not found.
        500:
            description: Error occurred.
    """
    category_exists = db.session.query(Category.id).filter_by(id=c_id).first() is not None
    if not category_exists:
        abort(404)

    try:
        page = request.args.get("page", default=1, type=int)

        products = (
            Product.query
            .join(subcategory_product)
            .join(category_subcategory, onclause=subcategory_product.c.subcategory_id == category_subcategory.c.subcategory_id)
            .filter(category_subcategory.c.category_id == c_id)
            .distinct()
            .order_by(Product.id.asc())
            .paginate(page=page, per_page=2, error_out=False)
        )

        return {
            "products": [p.to_json() for p in products]
        }, 200
    except:
        return "Error occured", 500


@app.route('/subcategory/create', methods=['POST'])
def create_subcategory():
    """
    Create Subcategory
    ---
    tags:
        - Subcategory
    description: Create a new subcategory.
    requestBody:
        required: true
        description: name - Name of the subcategory <br> categories - Array of category ids (optional) <br> products - Array of product ids (optional)
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - name
                    properties:
                        name:
                            type: string
                        categories:
                            type: array
                            items:
                                type: integer
                        products:
                            type: array
                            items:
                                type: integer
    responses:
        201:
            description: Subcategory created successfully.
        400:
            description: Invalid input.
        500:
            description: Error occurred.
    """
    if not request.json:
        abort(400)

    try:
        subcategory = Subcategory(
            name=request.json.get('name')
        )
        c_ids = request.json.get('categories')
        p_ids = request.json.get('products')
        if c_ids is not None:
            categories = Category.query.filter(Category.id.in_(c_ids))
            subcategory.categories.extend(categories)
        if p_ids is not None:
            products = Product.query.filter(Product.id.in_(p_ids))
            subcategory.products.extend(products)
        db.session.add(subcategory)
        db.session.commit()
        return jsonify(subcategory.to_json()), 201
    except:
        return "Error occured", 500


@app.route('/subcategories', methods=['GET'])
def get_all_subcategories():
    """
    Get All Subcategories
    ---
    tags:
        - Subcategory
    description: Get all subcategories.
    responses:
        200:
            description: A list of subcategories.
    """
    subcategories = Subcategory.query.order_by(Subcategory.name).all()
    return jsonify({"subcategories": [subcategory.to_json() for subcategory in subcategories]}), 200


@app.route('/subcategory/<int:sc_id>', methods=['GET'])
def get_subcategory(sc_id):
    """
    Get Subcategory
    ---
    tags:
        - Subcategory
    description: Get a subcategory by ID.
    parameters:
        - in: path
          name: sc_id
          required: true
          type: integer
          description: Subcategory ID
    responses:
        200:
            description: Subcategory retrieved successfully.
        404:
            description: Subcategory not found.
    """
    subcategory = Subcategory.query.get(sc_id)
    if subcategory is None:
        abort(404)
    return jsonify(subcategory.to_json()), 200


@app.route('/subcategory/<int:sc_id>/update', methods=['PUT'])
def update_subcategory(sc_id):
    """
    Update Subcategory
    ---
    tags:
        - Subcategory
    description: Update an existing subcategory.
    parameters:
        - in: path
          name: sc_id
          required: true
          type: integer
          description: Subcategory ID
    requestBody:
        required: true
        description: name - Name of the subcategory (optional) <br> categories - Array of category ids (optional) <br> products - Array of product ids (optional)
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        name:
                            type: string
                        categories:
                            type: array
                            items:
                                type: integer
                        products:
                            type: array
                            items:
                                type: integer
    responses:
        201:
            description: Subcategory updated successfully.
        400:
            description: Invalid input.
        404:
            description: Subcategory not found.
        500:
            description: Error occurred.
    """
    if not request.json:
        abort(400)

    subcategory = Subcategory.query.get(sc_id)
    if subcategory is None:
        abort(404)
    try:
        name = request.json.get('name')
        c_ids = request.json.get('categories')
        p_ids = request.json.get('products')
        if name is not None:
            subcategory.name = request.json.get('name')
        if c_ids is not None:
            categories = Category.query.filter(Category.id.in_(c_ids))
            subcategory.categories.extend(categories)
        if p_ids is not None:
            products = Product.query.filter(Product.id.in_(p_ids))
            subcategory.products.extend(products)
        db.session.commit()
        return jsonify(subcategory.to_json()), 201
    except:
        return "Error occured", 500


@app.route("/subcategory/<int:sc_id>", methods=["DELETE"])
def delete_subcategory(sc_id):
    """
    Delete Subcategory
    ---
    tags:
        - Subcategory
    description: Delete a subcategory by ID.
    parameters:
        - in: path
          name: sc_id
          required: true
          type: integer
          description: Subcategory ID
    responses:
        200:
            description: Subcategory deleted successfully.
        404:
            description: Subcategory not found.
        500:
            description: Error occurred.
    """
    subcategory = Subcategory.query.get(sc_id)
    if subcategory is None:
        abort(404)
    try:
        db.session.delete(subcategory)
        db.session.commit()
        return jsonify({'result': True}), 200
    except:
        return "Error occured", 500


@app.route('/subcategory/<int:sc_id>/categories', methods=['GET'])
def get_subcategory_categories(sc_id):
    """
    Get Categories related to a Subcategory.
    ---
    tags:
        - Subcategory
    description: Get Categories related to a Subcategory.
    parameters:
        - in: path
          name: sc_id
          required: true
          type: integer
          description: Subcategory ID
    responses:
        200:
            description: Categories retrieved successfully.
        404:
            description: Subcategory not found.
        500:
            description: Error occurred.
    """
    subcategory = Subcategory.query.get(sc_id)
    if subcategory is None:
        abort(404)

    try:
        return {
            "categories": [c.to_json() for c in subcategory.categories]
        }, 200
    except:
        return "Error occured", 500


@app.route('/subcategory/<int:sc_id>/products', methods=['GET'])
def get_subcategory_products(sc_id):
    """
    Get Products within a Subcategory.
    ---
    tags:
        - Subcategory
    description: Get products for a subcategory.
    parameters:
        - in: path
          name: sc_id
          required: true
          type: integer
          description: Subcategory ID
        - in: query
          name: page
          type: integer
          default: 1
          description: Page number
    responses:
        200:
            description: Products retrieved successfully.
        404:
            description: Subcategory not found.
        500:
            description: Error occurred.
    """
    subcategory = Subcategory.query.get(sc_id)
    if not subcategory:
        abort(404)

    try:
        page = request.args.get("page", default=1, type=int)
        products = subcategory.products.order_by(Product.id.asc()).paginate(page=page, per_page=2, error_out=False)
        return {
            "products": [p.to_json() for p in products]
        }, 200
    except:
        return "Error occured", 500


@app.route('/product/create', methods=['POST'])
def create_product():
    """
    Create Product
    ---
    tags:
        - Product
    description: Create a new product.
    requestBody:
        required: true
        description: name - Name of the product <br> description - Description of the product (optional) <br> subcategories - Array of subcategory ids (optional)
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - name
                    properties:
                        name:
                            type: string
                        description:
                            type: string
                        subcategories:
                            type: array
                            items:
                                type: integer
    responses:
        201:
            description: Product created successfully.
        400:
            description: Invalid input.
        500:
            description: Error occurred.
    """
    if not request.json:
        abort(400)

    try:
        product = Product(
            name=request.json.get('name'),
            description=request.json.get('description')
        )
        sc_ids = request.json.get('subcategories')
        if sc_ids is not None:
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids))
            product.subcategories.extend(subcategories)
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_json()), 201
    except:
        return "Error occured", 500


@app.route('/product/<int:p_id>', methods=['GET'])
def get_product(p_id):
    """
    Get Product
    ---
    tags:
        - Product
    description: Get a product by ID.
    parameters:
        - in: path
          name: p_id
          required: true
          type: integer
          description: Product ID
    responses:
        200:
            description: Product retrieved successfully.
        404:
            description: Product not found.
    """
    product = Product.query.get(p_id)
    if product is None:
        abort(404)
    return jsonify(product.to_json()), 200


@app.route('/product/<int:p_id>/update', methods=['PUT'])
def update_product(p_id):
    """
    Update Product
    ---
    tags:
        - Product
    description: Update an existing product.
    consumes:
        - application/json
    parameters:
        - in: path
          name: p_id
          required: true
          type: integer
          description: Product ID
    requestBody:
        required: true
        description: name - Name of the product (optional) <br> description = Description of the product (optional) <br> subcategories - Array of subcategory ids (optional)
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        name:
                            type: string
                        description:
                            type: string
                        subcategories:
                            type: array
                            items:
                                type: integer
    responses:
        201:
            description: Product updated successfully.
        400:
            description: Invalid input.
        404:
            description: Product not found.
        500:
            description: Error occurred.
    """
    if not request.json:
        abort(400)

    product = Product.query.get(p_id)
    if product is None:
        abort(404)
    try:
        name = request.json.get('name')
        description = request.json.get('description')
        sc_ids = request.json.get('subcategories')
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if sc_ids is not None:
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids))
            product.subcategories.extend(subcategories)
        db.session.commit()
        return jsonify(product.to_json()), 201
    except:
        return "Error occured", 500


@app.route("/product/<int:p_id>", methods=["DELETE"])
def delete_product(p_id):
    """
    Delete Product
    ---
    tags:
        - Product
    description: Delete a product by ID.
    parameters:
        - in: path
          name: p_id
          required: true
          type: integer
          description: Product ID
    responses:
        200:
            description: Product deleted successfully.
        404:
            description: Product not found.
        500:
            description: Error occurred.
    """
    product = Product.query.get(p_id)
    if product is None:
        abort(404)
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'result': True}), 200
    except:
        return "Error occured", 500


@app.route('/product/<string:name>', methods=['GET'])
def get_product_by_name(name):
    """
    Get Product by Name
    ---
    tags:
        - Product
    description: Get a product by name.
    parameters:
        - in: path
          name: name
          required: true
          type: string
          description: Product name
    responses:
        200:
            description: Product retrieved successfully.
        404:
            description: Product not found.
        500:
            description: Error occurred.
    """
    product = Product.query.filter(Product.name == name).first()
    if product is None:
        abort(404)

    try:
        product_json = product.to_json()
        subcategories = Subcategory.query.filter(Subcategory.id.in_(product_json["subcategories"]))
        c_ids = set(c.id for sc in subcategories for c in sc.categories)
        product_json["categories"] = list(c_ids)
        return product_json, 200
    except:
        return "Error occured", 500


@app.route('/products', methods=['GET'])
def get_all_products():
    """
    Get All Products
    ---
    tags:
        - Product
    description: Get all products.
    parameters:
        - in: query
          name: page
          type: integer
          default: 1
          description: Page number
    responses:
        200:
            description: A list of products for that page.
    """
    page = request.args.get("page", default=1, type=int)
    products = Product.query.order_by(Product.id.asc()).paginate(page=page, per_page=2, error_out=False)
    return jsonify({"products": [product.to_json() for product in products]}), 200


@app.route('/product/<int:p_id>/subcategories', methods=['GET'])
def get_product_subcategories(p_id):
    """
    Get Subcategories related to a Product.
    ---
    tags:
        - Product
    description: Get Subcategories related to a Product.
    parameters:
        - in: path
          name: p_id
          required: true
          type: integer
          description: Product ID
    responses:
        200:
            description: Subcategories retrieved successfully.
        404:
            description: Product not found.
        500:
            description: Error occurred.
    """
    product = Product.query.get(p_id)
    if product is None:
        abort(404)

    try:
        return {
            "subcategories": [sc.to_json() for sc in product.subcategories]
        }, 200
    except:
        return "Error occured", 500
