import itertools

from flask import request, abort, jsonify

from __main__ import app, db
from models import Category, Subcategory, Product


@app.route('/', methods=['GET'])
def index():
    return "Ecommerce REST API"


@app.route('/category/create', methods=['POST'])
def create_category():
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


@app.route('/categories', methods=['GET'])
def get_all_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify({"categories": [category.to_json() for category in categories]}), 200


@app.route('/category/<int:c_id>', methods=['GET'])
def get_category(c_id):
    category = Category.query.get(c_id)
    if category is None:
        abort(404)
    return jsonify(category.to_json()), 200


@app.route('/category/<int:c_id>/update', methods=['PUT'])
def update_category(c_id):
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
    category = Category.query.get(c_id)
    if category is None:
        abort(404)
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'result': True}), 200
    except:
        return "Error occured", 500


@app.route('/subcategory/create', methods=['POST'])
def create_subcategory():
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
    subcategories = Subcategory.query.order_by(Subcategory.name).all()
    return jsonify({"subcategories": [subcategory.to_json() for subcategory in subcategories]}), 200


@app.route('/subcategory/<int:sc_id>', methods=['GET'])
def get_subcategory(sc_id):
    subcategory = Subcategory.query.get(sc_id)
    if subcategory is None:
        abort(404)
    return jsonify(subcategory.to_json()), 200


@app.route('/subcategory/<int:sc_id>/update', methods=['PUT'])
def update_subcategory(sc_id):
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
    subcategory = Subcategory.query.get(sc_id)
    if subcategory is None:
        abort(404)
    try:
        db.session.delete(subcategory)
        db.session.commit()
        return jsonify({'result': True}), 200
    except:
        return "Error occured", 500


@app.route('/product/create', methods=['POST'])
def create_product():
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


@app.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.order_by(Product.name).all()
    return jsonify({"products": [product.to_json() for product in products]}), 200


@app.route('/product/<int:p_id>', methods=['GET'])
def get_product(p_id):
    product = Product.query.get(p_id)
    if product is None:
        abort(404)
    return jsonify(product.to_json()), 200


@app.route('/product/<int:p_id>/update', methods=['PUT'])
def update_product(p_id):
    if not request.json:
        abort(400)

    product = Product.query.get(p_id)
    if product is None:
        abort(404)
    try:
        name = request.json.get('name')
        sc_ids = request.json.get('subcategories')
        if name is not None:
            product.name = name
        if sc_ids is not None:
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids))
            product.subcategories.extend(subcategories)
        db.session.commit()
        return jsonify(product.to_json()), 201
    except:
        return "Error occured", 500


@app.route("/product/<int:p_id>", methods=["DELETE"])
def delete_product(p_id):
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


@app.route('/subcategory/<int:sc_id>/products', methods=['GET'])
def get_subcategory_products(sc_id):
    subcategory = Subcategory.query.get(sc_id)
    if not subcategory:
        abort(404)

    try:
        page = request.args.get("page", default=1, type=int)
        return {
            "products": [p.id for p in subcategory.products.paginate(page=page, per_page=2)]
        }, 200
    except:
        return "Error occured", 500


@app.route('/category/<int:c_id>/products', methods=['GET'])
def get_category_products(c_id):
    category = Category.query.get(c_id)
    if not category:
        abort(404)

    try:
        page = request.args.get("page", default=1, type=int)
        gen = itertools.chain.from_iterable(sc.products for sc in category.subcategories)
        products = itertools.islice(gen, (page - 1) * 2, page * 2)
        return {
            "products": [p.id for p in products]
        }, 200
    except:
        return "Error occured", 500
