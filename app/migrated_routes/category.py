from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from psycopg2.errors import UniqueViolation
from sqlalchemy import UniqueConstraint, exists
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import (
    Category,
    Product,
    Subcategory,
    category_subcategory,
    subcategory_product,
)
from app.schemas import (
    CategoriesOut,
    CategoryIn,
    CategoryOut,
    PaginationArgs,
    ProductsOut,
    SubcategoriesOut,
)

bp = Blueprint("category", __name__)


@bp.route("")
class CategoryCollection(MethodView):
    init_every_request = False

    @staticmethod
    def _get_name_unique_constraint():
        name_col = Category.__table__.c.name
        return next(
            con
            for con in Category.__table__.constraints
            if isinstance(con, UniqueConstraint)
            and len(con.columns) == 1
            and con.columns.contains_column(name_col)
        )

    _NAME_UNIQUE_CONSTRAINT = _get_name_unique_constraint()

    @bp.response(200, CategoriesOut)
    def get(self):
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
        return {"categories": Category.query.all()}

    @jwt_required()
    @bp.arguments(CategoryIn)
    @bp.response(201, CategoryOut)
    def post(self, data):
        """
        Create Category
        ---
        tags:
            - Category
        description: Create a new category.
        security:
            - access_token: []
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
            401:
                description: Token expired, missing or invalid.
            500:
                description: Error occurred.
        """
        category = Category(name=data["name"])

        if sc_ids := data.get("subcategories"):
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids)).all()
            if len(subcategories) != len(sc_ids):
                abort(422, message="One or more subcategories not present")

            category.subcategories = subcategories

        try:
            db.session.add(category)
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == CategoryCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Category with this name already exists")
            raise ie

        return category


@bp.route("/<int:id>")
class CategoryById(MethodView):
    init_every_request = False

    def _get(self, id):
        return Category.query.get_or_404(id)

    @bp.response(200, CategoryOut)
    def get(self, id):
        """
        Get Category
        ---
        tags:
            - Category
        description: Get a category by ID.
        parameters:
            - in: path
              name: id
              required: true
              type: integer
              description: Category ID
        responses:
            200:
                description: Category retrieved successfully.
            404:
                description: Category not found.
        """
        return self._get(id)

    @jwt_required()
    @bp.arguments(CategoryIn(partial=("name",)))
    @bp.response(200, CategoryOut)
    def put(self, data, id):
        """
        Update Category
        ---
        tags:
            - Category
        description: Update an existing category.
        security:
            - access_token: []
        parameters:
            - in: path
              name: id
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
        category = self._get(id)
        if name := data.get("name"):
            category.name = name

        if sc_ids := data.get("subcategories"):
            subcategories = Subcategory.query.filter(Subcategory.id.in_(sc_ids)).all()
            if len(subcategories) != len(sc_ids):
                abort(422, message="One or more subcategories not present")

            category.subcategories.extend(subcategories)

        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == category_subcategory.primary_key.name
            ):
                abort(409, message="Category and subcategory already linked")
            raise ie

        return category

    @jwt_required()
    @bp.response(204)
    def delete(self, id):
        """
        Delete Category
        ---
        tags:
            - Category
        description: Delete a category by ID.
        security:
            - access_token: []
        parameters:
            - in: path
              name: id
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
        category = self._get(id)
        db.session.delete(category)
        db.session.commit()


@bp.route("/<int:id>/subcategories")
class CategorySubcategories(MethodView):
    init_every_request = False

    @bp.response(200, SubcategoriesOut)
    def get(self, id):
        """
        Get Subcategories within a Category.
        ---
        tags:
            - Category
        description: Get Subcategories within a Category.
        parameters:
            - in: path
              name: id
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
        category = Category.query.get_or_404(id)
        return {"subcategories": category.subcategories}


@bp.route("/<int:id>/products")
class CategoryProducts(MethodView):
    init_every_request = False
    _PER_PAGE = 10

    @bp.arguments(PaginationArgs, location="query", as_kwargs=True)
    @bp.response(200, ProductsOut)
    def get(self, id, page):
        """
        Get Products within a Category.
        ---
        tags:
            - Category
        description: Get Products for a Category.
        parameters:
            - in: path
              name: id
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
        category_exists = db.session.query(exists().where(Category.id == id)).scalar()
        if not category_exists:
            abort(404)

        products = (
            Product.query.join(subcategory_product)
            .join(
                category_subcategory,
                onclause=subcategory_product.c.subcategory_id
                == category_subcategory.c.subcategory_id,
            )
            .filter(category_subcategory.c.category_id == id)
            .distinct()
            .order_by(Product.id.asc())
            .paginate(page=page, per_page=CategoryProducts._PER_PAGE, error_out=False)
        )

        return {"products": products}
