from marshmallow import Schema, ValidationError, fields, pre_load, validates
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field

from app.models import Category, Product, Subcategory


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
        if "name" in data:
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
        if "name" in data:
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


class PaginationArgs(Schema):
    page = fields.Int(load_default=1)
