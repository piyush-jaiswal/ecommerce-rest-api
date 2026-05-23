from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from psycopg2.errors import UniqueViolation
from sqlakeyset import get_page
from sqlalchemy import UniqueConstraint, exists
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import (
    Category,
    Product,
    Subcategory,
    category_subcategory,
)
from app.schemas import (
    CategoriesOut,
    CategoryIn,
    CategoryOut,
    CategoryPatchIn,
    PaginationArgs,
    ProductsOut,
    SubcategoriesOut,
)

bp = Blueprint("Category", __name__)


@bp.route("/")
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

    @bp.doc(summary="Get All Categories")
    @bp.response(200, CategoriesOut)
    def get(self):
        return {"categories": Category.query.all()}

    @jwt_required()
    @bp.doc(summary="Create Category", security=[{"access_token": []}])
    @bp.arguments(CategoryIn)
    @bp.response(201, CategoryOut)
    def post(self, data):
        category = Category(name=data["name"])

        if sc_ids := data.get("subcategories"):
            sc_ids = set(sc_ids)
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
            raise

        return category


@bp.route("/<int:id>")
class CategoryById(MethodView):
    init_every_request = False

    def _get(self, id):
        return Category.query.get_or_404(id)

    @bp.doc(summary="Get Category")
    @bp.response(200, CategoryOut)
    def get(self, id):
        return self._get(id)

    @jwt_required()
    @bp.doc(summary="Update Category", security=[{"access_token": []}])
    @bp.arguments(CategoryIn(partial=("name",)))
    @bp.response(200, CategoryOut)
    def put(self, data, id):
        category = self._get(id)
        if name := data.get("name"):
            category.name = name

        with db.session.no_autoflush:
            if "subcategories" in data:
                sc_ids = set(data["subcategories"])
                subcategories = Subcategory.query.filter(
                    Subcategory.id.in_(sc_ids)
                ).all()
                if len(subcategories) != len(sc_ids):
                    abort(422, message="One or more subcategories not present")
                category.subcategories = subcategories

        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == CategoryCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Category with this name already exists")
            raise

        return category

    @jwt_required()
    @bp.doc(summary="Partially update Category", security=[{"access_token": []}])
    @bp.arguments(CategoryPatchIn)
    @bp.response(200, CategoryOut)
    def patch(self, data, id):
        category = self._get(id)

        if "name" in data:
            category.name = data["name"]

        with db.session.no_autoflush:
            add_ids = set(data.get("subcategories_add", []))
            remove_ids = set(data.get("subcategories_remove", []))

            overlap = add_ids & remove_ids
            if overlap:
                abort(
                    422,
                    message=f"Cannot add and remove the same subcategory: {sorted(overlap)}",
                )

            if remove_ids:
                db.session.execute(
                    category_subcategory.delete().where(
                        category_subcategory.c.category_id == category.id,
                        category_subcategory.c.subcategory_id.in_(remove_ids),
                    )
                )

            if add_ids:
                existing_ids = {
                    row[0]
                    for row in db.session.query(category_subcategory.c.subcategory_id)
                    .filter(
                        category_subcategory.c.category_id == category.id,
                        category_subcategory.c.subcategory_id.in_(add_ids),
                    )
                    .all()
                }
                new_ids = [aid for aid in add_ids if aid not in existing_ids]
                if new_ids:
                    to_add = Subcategory.query.filter(Subcategory.id.in_(new_ids)).all()
                    if len(to_add) != len(new_ids):
                        abort(422, message="One or more subcategories not present")
                    db.session.execute(
                        category_subcategory.insert().values(
                            [
                                {"category_id": category.id, "subcategory_id": s.id}
                                for s in to_add
                            ]
                        )
                    )

        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == CategoryCollection._NAME_UNIQUE_CONSTRAINT.name
            ):
                abort(409, message="Category with this name already exists")

            # Only reachable in race conditions; normal case handled by upfront filter
            if (
                isinstance(ie.orig, UniqueViolation)
                and ie.orig.diag.constraint_name
                == category_subcategory.primary_key.name
            ):
                abort(409, message="Category and subcategory already linked")
            raise

        return category

    @jwt_required()
    @bp.doc(summary="Delete Category", security=[{"access_token": []}])
    @bp.response(204)
    def delete(self, id):
        category = self._get(id)
        db.session.delete(category)
        db.session.commit()


@bp.route("/<int:id>/subcategories")
class CategorySubcategories(MethodView):
    init_every_request = False

    @bp.doc(summary="Get Subcategories within a Category")
    @bp.response(200, SubcategoriesOut)
    def get(self, id):
        category = Category.query.get_or_404(id)
        return {"subcategories": category.subcategories}


@bp.route("/<int:id>/products")
class CategoryProducts(MethodView):
    init_every_request = False
    _PER_PAGE = 10

    @bp.doc(summary="Get Products within a Category")
    @bp.arguments(PaginationArgs, location="query", as_kwargs=True)
    @bp.response(200, ProductsOut)
    def get(self, id, cursor):
        category_exists = db.session.query(exists().where(Category.id == id)).scalar()
        if not category_exists:
            abort(404)

        products = Product.query.filter(
            Product.subcategories.any(Subcategory.categories.any(id=id))
        ).order_by(Product.id.asc())
        page = get_page(products, per_page=CategoryProducts._PER_PAGE, page=cursor)

        return {"products": page, "cursor": page.paging}
