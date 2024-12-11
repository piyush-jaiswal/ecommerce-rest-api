from datetime import datetime
from app import db
from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError


@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    response = jsonify({"error": "There is a conflict with the database integrity", "details": str(error.orig)})
    response.status_code = 400
    return response
  
category_subcategory = db.Table("category_subcategory",
                                db.Column("category_id", db.Integer, db.ForeignKey("category.id", ondelete="CASCADE"), index=True),
                                db.Column("subcategory_id", db.Integer, db.ForeignKey("subcategory.id", ondelete="CASCADE"), index=True))

subcategory_product = db.Table("subcategory_product",
                                db.Column("subcategory_id", db.Integer, db.ForeignKey("subcategory.id", ondelete="CASCADE"), index=True),
                                db.Column("product_id", db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), index=True))


class BaseModel(db.Model):
    __abstract__ = True

    def to_json(self):
        return {col.name: getattr(self, col.name).isoformat() if isinstance(getattr(self, col.name), datetime) 
                else getattr(self, col.name) 
                for col in self.__table__.columns}
        
class Category(BaseModel):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subcategories = db.relationship("Subcategory", secondary=category_subcategory, back_populates="categories", lazy='joined')



class Subcategory(BaseModel):
    __tablename__ = 'subcategory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship("Product", secondary=subcategory_product, back_populates="subcategories", lazy='joined')



class Product(BaseModel):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

  
