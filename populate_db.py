from faker import Faker
from app import create_app, db
from app.models import Category, Subcategory, Product, category_subcategory, subcategory_product
import random


app = create_app()
fake = Faker()


def create_categories(num=5):
    categories = []
    for _ in range(num):
        category = Category(name=fake.unique.company())
        categories.append(category)
    
    db.session.add_all(categories)
    return categories


def create_subcategories(num=10):
    subcategories = []
    for _ in range(num):
        subcategory = Subcategory(name=fake.unique.city())
        subcategories.append(subcategory)
    
    db.session.add_all(subcategories)
    return subcategories


def create_products(num=50):
    products = []
    for _ in range(num):
        product = Product(name=fake.unique.catch_phrase(), description=fake.text(max_nb_chars=500))
        products.append(product)
    
    db.session.add_all(products)
    return products


def create_relationships(categories, subcategories, products, max_category_association=3, max_subcategory_association=5):
    for subcategory in subcategories:
        num_categories = random.randint(1, max_category_association)
        associated_categories = random.sample(categories, num_categories)
        subcategory.categories.extend(associated_categories)

    for product in products:
        num_subcategories = random.randint(1, max_subcategory_association)
        associated_subcategories = random.sample(subcategories, num_subcategories)
        product.subcategories.extend(associated_subcategories)


def main():
    with app.app_context():
        category_subcategory.drop(db.engine, checkfirst=True)
        subcategory_product.drop(db.engine, checkfirst=True)
        Category.__table__.drop(db.engine, checkfirst=True)
        Subcategory.__table__.drop(db.engine, checkfirst=True)
        Product.__table__.drop(db.engine, checkfirst=True)

        Category.__table__.create(db.engine)
        Subcategory.__table__.create(db.engine)
        Product.__table__.create(db.engine)
        category_subcategory.create(db.engine)
        subcategory_product.create(db.engine)

        categories = create_categories(50)
        subcategories = create_subcategories(100)
        products = create_products(10000)
        
        create_relationships(categories, subcategories, products)
        
        db.session.commit()
        print("db populated!")


if __name__ == "__main__":
    main()
