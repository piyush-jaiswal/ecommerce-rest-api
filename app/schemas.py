import base64

from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates
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

    name = auto_field()
    subcategories = fields.List(fields.Int())

    @pre_load
    def strip_strings(self, data, **kwargs):
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()

        return data

    @validates("name")
    def validate_str_min_len(self, value, data_key):
        if len(value) < 1:
            raise ValidationError("Cannot be empty")


class SubcategoryOut(SQLAlchemyAutoSchema):
    class Meta:
        model = Subcategory


class SubcategoriesOut(Schema):
    subcategories = fields.List(fields.Nested(SubcategoryOut))


class SubcategoryIn(SQLAlchemySchema):
    class Meta:
        model = Subcategory

    name = auto_field()
    categories = fields.List(fields.Int())
    products = fields.List(fields.Int())

    @pre_load
    def strip_strings(self, data, **kwargs):
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()

        return data

    @validates("name")
    def validate_str_min_len(self, value, data_key):
        if len(value) < 1:
            raise ValidationError("Cannot be empty")


class ProductOut(SQLAlchemyAutoSchema):
    class Meta:
        model = Product


class ProductsOut(Schema):
    products = fields.List(fields.Nested(ProductOut))
    cursor = Cursor(required=False)  # require false for getting product by name


class ProductIn(SQLAlchemySchema):
    class Meta:
        model = Product

    name = auto_field()
    description = auto_field()
    subcategories = fields.List(fields.Int())

    @pre_load
    def strip_strings(self, data, **kwargs):
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
        if "description" in data and data["description"] is not None:
            data["description"] = data["description"].strip()

        return data

    @validates("name")
    def validate_str_min_len(self, value, data_key):
        if len(value) < 1:
            raise ValidationError("Cannot be empty")


class NameArgs(Schema):
    name = fields.Str(load_default=None)


class PaginationArgs(Schema):
    cursor = Cursor(load_default=None)


class AuthIn(SQLAlchemySchema):
    class Meta:
        model = User

    # email validation handled in User model
    email = auto_field()
    password = fields.Str(required=True, validate=validate.Length(min=1))

    @pre_load
    def strip_strings(self, data, **kwargs):
        if "email" in data and data["email"] is not None:
            data["email"] = data["email"].strip()
        return data


class AuthOut(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()
