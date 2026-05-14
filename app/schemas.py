import base64

from marshmallow import Schema, ValidationError, fields, validate
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from sqlakeyset import BadBookmark, unserialize_bookmark

from app.models import Category, Product, Subcategory, User


class Cursor(fields.Field[dict]):
    def _serialize(self, paging, attr, obj, **kwargs):
        def encode(s):
            bytes = s.encode("utf-8")
            return base64.urlsafe_b64encode(bytes).decode("utf-8")

        if paging is None:
            return None

        return {
            "next": encode(paging.bookmark_next) if paging.has_next else None,
            "prev": encode(paging.bookmark_previous) if paging.has_previous else None,
        }

    def _deserialize(self, cursor, attr, data, **kwargs):
        if cursor is None:
            return None

        try:
            decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
            marker_serialized = decoded_bytes.decode("utf-8")
            return unserialize_bookmark(marker_serialized)
        except (TypeError, ValueError, KeyError, BadBookmark) as ex:
            raise ValidationError("Invalid cursor") from ex


class CategoryOut(SQLAlchemyAutoSchema):
    class Meta:
        model = Category


class CategoriesOut(Schema):
    categories = fields.List(fields.Nested(CategoryOut))


class CategoryIn(SQLAlchemySchema):
    class Meta:
        model = Category

    name = auto_field(pre_load=str.strip, validate=validate.Length(min=1))
    subcategories = fields.List(fields.Int())


class SubcategoryOut(SQLAlchemyAutoSchema):
    class Meta:
        model = Subcategory


class SubcategoriesOut(Schema):
    subcategories = fields.List(fields.Nested(SubcategoryOut))


class SubcategoryIn(SQLAlchemySchema):
    class Meta:
        model = Subcategory

    name = auto_field(pre_load=str.strip, validate=validate.Length(min=1))
    categories = fields.List(fields.Int())
    products = fields.List(fields.Int())


class ProductOut(SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        exclude = ("search_vector",)


class ProductsOut(Schema):
    products = fields.List(fields.Nested(ProductOut))
    cursor = Cursor()


class ProductIn(SQLAlchemySchema):
    class Meta:
        model = Product

    name = auto_field(pre_load=str.strip, validate=validate.Length(min=1))
    description = auto_field(pre_load=lambda x: x.strip() if isinstance(x, str) else x)
    subcategories = fields.List(fields.Int())


class SearchArgs(Schema):
    q = fields.Str(required=True, pre_load=str.strip, validate=validate.Length(min=1))


class PaginationArgs(Schema):
    cursor = Cursor(load_default=None)


class AuthIn(SQLAlchemySchema):
    class Meta:
        model = User

    # email validation handled in User model
    email = auto_field(pre_load=str.strip)
    password = fields.Str(required=True, validate=validate.Length(min=1))


class AuthOut(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()
