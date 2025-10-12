from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from psycopg2.errors import UniqueViolation
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import (
    Product,
    Subcategory,
    subcategory_product,
)
from app.schemas import (
    NameArgs,
    PaginationArgs,
    ProductIn,
    ProductOut,
    ProductsOut,
    SubcategoriesOut,
)

bp = Blueprint("product", __name__)


@bp.route("")
class ProductCollection(MethodView):
    init_every_request = False
    _PER_PAGE = 10

    @staticmethod
    def _get_name_unique_constraint():
        name_col = Product.__table__.c.name
        return next(
            con
            for con in Product.__table__.constraints
            if isinstance(con, UniqueConstraint)
            and len(con.columns) == 1
            and con.columns.contains_column(name_col)
        )

    _NAME_UNIQUE_CONSTRAINT = _get_name_unique_constraint()

    def _get_by_name(self, name):
        return Product.query.filter(Product.name == name)

    @bp.arguments(NameArgs, location="query", as_kwargs=True)
    @bp.arguments(PaginationArgs, location="query", as_kwargs=True)
    @bp.response(200, ProductsOut)
    def get(self, name, page):
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
            - in: query
              name: name
              type: string
              description: Name
        responses:
            200:
                description: Product by name or a paginated list of all products.
        """
        if name is not None:
            products = self._get_by_name(name)
        else:
            products = Product.query.order_by(Product.id.asc()).paginate(
                page=page, per_page=ProductCollection._PER_PAGE, error_out=False
            )

        return {"products": products}

    @jwt_required()
    @bp.arguments(ProductIn)
    @bp.response(201, ProductOut)
    def post(self, data):
        """
        Create Product
        ---
        tags:
            - Product
        description: Create a new product.
        security:
            - access_token: []
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
            401:
                description: Token expired, missing or invalid.
            500:
                description: Error occurred.
        """
        product = Product(name=data["name"], description=data.get("description"))

        if sc_ids := data.get("subcategories"):
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids)).all()
            if len(subcategories) != len(sc_ids):
                abort(422, message="One or more subcategories not present")
            product.subcategories = subcategories

        try:
            db.session.add(product)
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == ProductCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Product with this name already exists")
            raise

        return product


@bp.route("/<int:id>")
class ProductById(MethodView):
    init_every_request = False

    def _get(self, id):
        return Product.query.get_or_404(id)

    @bp.response(200, ProductOut)
    def get(self, id):
        """
        Get Product
        ---
        tags:
            - Product
        description: Get a product by ID.
        parameters:
            - in: path
              name: id
              required: true
              type: integer
              description: Product ID
        responses:
            200:
                description: Product retrieved successfully.
            404:
                description: Product not found.
        """
        return self._get(id)

    @jwt_required()
    @bp.arguments(ProductIn(partial=("name",)))
    @bp.response(200, ProductOut)
    def put(self, data, id):
        """
        Update Product
        ---
        tags:
            - Product
        description: Update an existing product.
        security:
            - access_token: []
        consumes:
            - application/json
        parameters:
            - in: path
              name: id
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
        product = self._get(id)

        if name := data.get("name"):
            product.name = name
        if "description" in data:
            product.description = data["description"]

        with db.session.no_autoflush:
            if sc_ids := data.get("subcategories"):
                subcategories = Subcategory.query.filter(
                    Subcategory.id.in_(sc_ids)
                ).all()
                if len(subcategories) != len(sc_ids):
                    abort(422, message="One or more subcategories not present")
                product.subcategories.extend(subcategories)

        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == ProductCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Product with this name already exists")
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name == subcategory_product.primary_key.name
            ):
                abort(409, message="Product and subcategory already linked")
            raise

        return product

    @jwt_required()
    @bp.response(204)
    def delete(self, id):
        """
        Delete Product
        ---
        tags:
            - Product
        description: Delete a product by ID.
        security:
            - access_token: []
        parameters:
            - in: path
              name: id
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
        product = self._get(id)
        db.session.delete(product)
        db.session.commit()


@bp.route("/<int:id>/subcategories")
class ProductSubcategories(MethodView):
    init_every_request = False

    @bp.response(200, SubcategoriesOut)
    def get(self, id):
        """
        Get Subcategories related to a Product.
        ---
        tags:
            - Product
        description: Get Subcategories related to a Product.
        parameters:
            - in: path
              name: id
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
        product = Product.query.get_or_404(id)
        return {"subcategories": product.subcategories}
