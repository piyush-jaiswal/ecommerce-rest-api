from datetime import datetime

from sqlalchemy import CheckConstraint, Index
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from email_normalize import normalize

from app import db


class ConstraintFactory:
    @staticmethod
    def non_empty_string(column_name):
        constraint_name = f'{column_name}_non_empty'
        return CheckConstraint(f"TRIM({column_name}) != ''", name=constraint_name)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    email_normalized = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        ConstraintFactory.non_empty_string('email'),
        ConstraintFactory.non_empty_string('email_normalized'),
        ConstraintFactory.non_empty_string('password_hash')
    )

    # Does not check for non-deliverable mails. Use check_deliverability or resolve for that which does DNS checks
    # For more stricter validation, use confirmation emails, or a third party API
    @staticmethod
    def _normalize_email(email):
        # Follows RFCs, allows aliases and only lowers the domain part
        validated = validate_email(email, check_deliverability=False)
        # Lowers the local part and normalizes, removes aliases for popular email providers (gmail, yahoo etc)
        normalized = normalize(validated.email, resolve=False)
        return normalized
    
    @staticmethod
    def get(email):
        try:
            email_normalized = User._normalize_email(email)
        except EmailNotValidError:
            return None
        return User.query.filter_by(email_normalized=email_normalized).scalar()
    
    def set_email(self, email):
        self.email_normalized = self._normalize_email(email)
        self.email = email

    def set_password(self, password):
        # scrypt stores salt with the hash, which it uses to verify the password
        self.password_hash = generate_password_hash(password, method='scrypt')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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

    __table_args__ = (
        ConstraintFactory.non_empty_string('name'),
    )


class Subcategory(db.Model):
    __tablename__ = 'subcategory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    categories = db.relationship("Category", secondary=category_subcategory, back_populates="subcategories", lazy='dynamic', passive_deletes=True)
    products = db.relationship("Product", secondary=subcategory_product, back_populates="subcategories", lazy='dynamic', passive_deletes=True)

    __table_args__ = (
        ConstraintFactory.non_empty_string('name'),
    )


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False ,default=datetime.utcnow)
    subcategories = db.relationship("Subcategory", secondary=subcategory_product, back_populates="products", lazy='dynamic', passive_deletes=True)

    __table_args__ = (
        ConstraintFactory.non_empty_string('name'),
    )
