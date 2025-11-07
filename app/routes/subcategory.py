from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from psycopg2.errors import UniqueViolation
from sqlakeyset import get_page
from sqlalchemy import UniqueConstraint
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
    PaginationArgs,
    ProductsOut,
    SubcategoriesOut,
    SubcategoryIn,
    SubcategoryOut,
)

bp = Blueprint("Subcategory", __name__)


@bp.route("/")
class SubcategoryCollection(MethodView):
    init_every_request = False

    @staticmethod
    def _get_name_unique_constraint():
        name_col = Subcategory.__table__.c.name
        return next(
            con
            for con in Subcategory.__table__.constraints
            if isinstance(con, UniqueConstraint)
            and len(con.columns) == 1
            and con.columns.contains_column(name_col)
        )

    _NAME_UNIQUE_CONSTRAINT = _get_name_unique_constraint()

    @bp.doc(summary="Get All Subcategories")
    @bp.response(200, SubcategoriesOut)
    def get(self):
        return {"subcategories": Subcategory.query.all()}

    @jwt_required()
    @bp.doc(summary="Create Subcategory", security=[{"access_token": []}])
    @bp.arguments(SubcategoryIn)
    @bp.response(201, SubcategoryOut)
    def post(self, data):
        subcategory = Subcategory(name=data["name"])

        if c_ids := data.get("categories"):
            categories = Category.query.filter(Category.id.in_(c_ids)).all()
            if len(categories) != len(c_ids):
                abort(422, message="One or more categories not present")
            subcategory.categories = categories

        if p_ids := data.get("products"):
            products = Product.query.filter(Product.id.in_(p_ids)).all()
            if len(products) != len(p_ids):
                abort(422, message="One or more products not present")
            subcategory.products = products

        try:
            db.session.add(subcategory)
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == SubcategoryCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Subcategory with this name already exists")
            raise

        return subcategory


@bp.route("/<int:id>")
class SubcategoryById(MethodView):
    init_every_request = False

    def _get(self, id):
        return Subcategory.query.get_or_404(id)

    @bp.doc(summary="Get Subcategory")
    @bp.response(200, SubcategoryOut)
    def get(self, id):
        return self._get(id)

    @jwt_required()
    @bp.doc(summary="Update Subcategory", security=[{"access_token": []}])
    @bp.arguments(SubcategoryIn(partial=("name",)))
    @bp.response(200, SubcategoryOut)
    def put(self, data, id):
        subcategory = self._get(id)
        if name := data.get("name"):
            subcategory.name = name

        with db.session.no_autoflush:
            if c_ids := data.get("categories"):
                categories = Category.query.filter(Category.id.in_(c_ids)).all()
                if len(categories) != len(c_ids):
                    abort(422, message="One or more categories not present")
                subcategory.categories.extend(categories)

            if p_ids := data.get("products"):
                products = Product.query.filter(Product.id.in_(p_ids)).all()
                if len(products) != len(p_ids):
                    abort(422, message="One or more products not present")
                subcategory.products.extend(products)

        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == SubcategoryCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Subcategory with this name already exists")
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == category_subcategory.primary_key.name
            ):
                abort(409, message="Subcategory and category already linked")
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name == subcategory_product.primary_key.name
            ):
                abort(409, message="Subcategory and product already linked")
            raise

        return subcategory

    @jwt_required()
    @bp.doc(summary="Delete Subcategory", security=[{"access_token": []}])
    @bp.response(204)
    def delete(self, id):
        subcategory = self._get(id)
        db.session.delete(subcategory)
        db.session.commit()


@bp.route("/<int:id>/categories")
class SubcategoryCategories(MethodView):
    init_every_request = False

    @bp.doc(summary="Get Categories related to a Subcategory")
    @bp.response(200, CategoriesOut)
    def get(self, id):
        subcategory = Subcategory.query.get_or_404(id)
        return {"categories": subcategory.categories}


@bp.route("/<int:id>/products")
class SubcategoryProducts(MethodView):
    init_every_request = False
    _PER_PAGE = 10

    @bp.doc(summary="Get Products within a Subcategory")
    @bp.arguments(PaginationArgs, location="query", as_kwargs=True)
    @bp.response(200, ProductsOut)
    def get(self, id, cursor):
        subcategory = Subcategory.query.get_or_404(id)
        products = subcategory.products.order_by(Product.id.asc())
        page = get_page(products, per_page=SubcategoryProducts._PER_PAGE, page=cursor)

        return {"products": page, "cursor": page.paging}
