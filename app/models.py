from datetime import datetime

from sqlalchemy import Index

from app import db


# https://stackoverflow.com/questions/2190272/sql-many-to-many-table-primary-key
category_subcategory = db.Table("category_subcategory",
                                db.Column("category_id", db.Integer, db.ForeignKey("category.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                                db.Column("subcategory_id", db.Integer, db.ForeignKey("subcategory.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                                Index("category_subcategory_subcategory_id_idx", "subcategory_id", "category_id"))

subcategory_product = db.Table("subcategory_product",
                                db.Column("subcategory_id", db.Integer, db.ForeignKey("subcategory.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                                db.Column("product_id", db.Integer, db.ForeignKey("product.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
                                Index("subcategory_product_product_id_idx", "product_id", "subcategory_id"))


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)   # unique automatically creates a unique index
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    subcategories = db.relationship("Subcategory", secondary=category_subcategory, back_populates="categories", lazy='dynamic', passive_deletes=True)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'subcategories': [subcategory.id for subcategory in self.subcategories]
        }


class Subcategory(db.Model):
    __tablename__ = 'subcategory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    categories = db.relationship("Category", secondary=category_subcategory, back_populates="subcategories", lazy='dynamic', passive_deletes=True)
    products = db.relationship("Product", secondary=subcategory_product, back_populates="subcategories", lazy='dynamic', passive_deletes=True)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'categories': [c.id for c in self.categories],
            'products': [p.id for p in self.products]
        }


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False ,default=datetime.utcnow)
    subcategories = db.relationship("Subcategory", secondary=subcategory_product, back_populates="products", lazy='dynamic', passive_deletes=True)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'subcategories': [s.id for s in self.subcategories]
        }
