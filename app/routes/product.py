from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from psycopg2.errors import UniqueViolation
from sqlakeyset import get_page
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

bp = Blueprint("Product", __name__)


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

    @bp.doc(
        summary="Get All Products",
        description="If name is passed, filters the result to that single product, if present",
    )
    @bp.arguments(NameArgs, location="query", as_kwargs=True)
    @bp.arguments(PaginationArgs, location="query", as_kwargs=True)
    @bp.response(200, ProductsOut)
    def get(self, name, cursor):
        if name is not None:
            products = self._get_by_name(name)
            return {"products": products}
        else:
            products = Product.query.order_by(Product.id.asc())
            page = get_page(products, per_page=ProductCollection._PER_PAGE, page=cursor)
            return {"products": page, "cursor": page.paging}

    @jwt_required()
    @bp.doc(summary="Create Product", security=[{"access_token": []}])
    @bp.arguments(ProductIn)
    @bp.response(201, ProductOut)
    def post(self, data):
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

    @bp.doc(summary="Get Product")
    @bp.response(200, ProductOut)
    def get(self, id):
        return self._get(id)

    @jwt_required()
    @bp.doc(summary="Update Product", security=[{"access_token": []}])
    @bp.arguments(ProductIn(partial=("name",)))
    @bp.response(200, ProductOut)
    def put(self, data, id):
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
    @bp.doc(summary="Delete Product", security=[{"access_token": []}])
    @bp.response(204)
    def delete(self, id):
        product = self._get(id)
        db.session.delete(product)
        db.session.commit()


@bp.route("/<int:id>/subcategories")
class ProductSubcategories(MethodView):
    init_every_request = False

    @bp.doc(summary="Get Subcategories related to a Product")
    @bp.response(200, SubcategoriesOut)
    def get(self, id):
        product = Product.query.get_or_404(id)
        return {"subcategories": product.subcategories}
