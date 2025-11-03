<h1>Ecommerce REST API</h1>

[![Tests](https://github.com/piyush-jaiswal/ecommerce-rest-api/actions/workflows/tests.yml/badge.svg)](https://github.com/piyush-jaiswal/ecommerce-rest-api/actions/workflows/tests.yml)
[![Vercel Production Deployment](https://github.com/piyush-jaiswal/ecommerce-rest-api/actions/workflows/deploy_production.yml/badge.svg)](https://github.com/piyush-jaiswal/ecommerce-rest-api/actions/workflows/deploy_production.yml)

RESTful HTTP API using Python Flask that allows users to manage their ecommerce platform.
<br>

Ability to create, read, update, and delete products, categories and subcategories. A category can have multiple subcategories and a subcategory can belong to multiple categories. Products can belong to multiple categories and subcategories.
<br></br>
Fetching a product fetches the details of categories and subcategories it belongs to. Provides the ability to search for products by name, category and subcategories.
<br></br>
Paginates result using cursor based pagination when products are fetched by categories, subcategories or themselves.

Deployed as a vercel function with Postgres: [ecommerce-rest-api-five.vercel.app](https://ecommerce-rest-api-five.vercel.app)
<br> Documented with Swagger UI.
<br><br>

### Requirements
This project is written in `Python 3.12.1`

```bash
pip install -r requirements.txt
```
`requirements.txt` contains an adapter for PostgreSQL by default.

<br/>

### Usage

Copy `.env.example` and rename to `.env`. Provide your database URL to the `SQLALCHEMY_DATABASE_URI` environment variable.

Create database tables:

```bash
flask db upgrade head
```

(Optional) Populate database with fake data :

```bash
pip install -r requirements-dev.txt
python populate_db.py
```

Set `JWT_SECRET_KEY` environment variable. Run this in a python shell to generate sample keys:

```python
import secrets
secrets.token_urlsafe(32) # 'fP-3vOuhEr7Nl9DdJiX5XyjOedquOrifDps2KS34Wu0'
```

Start the server: (Runs on 127.0.0.1:5000)

```bash
flask --app app run [--debug]
``` 

Test the API using Swagger UI (`/` route), Postman, cURL or your preferred HTTP client.

<br/>

### Endpoints

#### Fetch products using name, category, subcategory
- [GET] `/products?name=<name: string>` - Get product with name: `name` <br/><br/>
- [GET] `/subcategories/<subcategory_id: int>/products` - Get first page of products within subcategory `subcategory_id`. <br/><br/>
- [GET] `/subcategories/<subcategory_id: int>/products?cursor=<cursor: str>` - Get products paginated using cursor within subcategory `subcategory_id`. Next and previous page `cursors` provided in responses. <br/><br/>
- [GET] `/categories/<category_id: int>/products` - Get first page of products within category `category_id`. <br/><br/>
- [GET] `/categories/<category_id: int>/products?cursor=<cursor: str>` - Get products paginated using cursor within category `category_id`. Next and previous page `cursors` provided in responses. <br/><br/>


#### Authorization
``Protected`` endpoints require the following header:
  `Authorization: Bearer <access_token>`

``Refresh protected`` endpoints requires the following header:
  `Authorization: Bearer <refresh_token>`
<br><br>

#### Authentication
- [POST] `/auth/register` - Register a new user.
  ```
  {
    "email": "user@example.com",
    "password": "your_password"
  }
  ```

- [POST] `/auth/login` - Login a user and get access and refresh tokens.
  ```
  {
    "email": "user@example.com",
    "password": "your_password"
  }
  ```

- [POST] `/auth/refresh` (Refresh protected) - Get new access token using a refresh token.
  
<br/>

#### Category
- [GET] `/categories` - Get all categories
- [GET] `/categories/(int: category_id)` - Get category with category_id
- [GET] `/categories/(int: category_id)/subcategories` - Get subcategories within a category_id.
- [DELETE] `/categories/(int: category_id)` (Protected) - Delete category with category_id

- [POST] `/categories` (Protected) - Create a new category
  ```
  {
    "name": "name",
    "subcategories": [<subcategory ids>] //optional
  }
  ```

- [PUT] `/categories/(int: category_id)` (Protected) - Update category with category_id
  ```
  {
    "name": "name",
    "subcategories": [<subcategory ids>] //optional
  }
  ```

<br/>

#### Subcategory
- [GET] `/subcategories` - Get all subcategories
- [GET] `/subcategories/(int: subcategory_id)` - Get subcategory with subcategory_id
- [GET] `/subcategories/(int: subcategory_id)/categories` - Get categories related to subcategory_id
- [DELETE] `/subcategories/(int: subcategory_id)` (Protected) - Delete subcategory with subcategory_id

- [POST] `/subcategories` (Protected) - Create a new subcategory
  ```
  {
    "name": "name",
    "categories": [(category ids)], //optional
    "products": [<product ids>] // optional
  }
  ```

- [PUT] `/subcategories/(int: subcategory_id)` (Protected) - Update subcategory with subcategory_id
  ```
  {
    "name": "name",
    "categories": [<category ids>], //optional
    "products": [<product ids>] // optional
  }
  ```


<br/>

#### Product
- [GET] `/products` - Get first page of products
- [GET] `/products?cursor=<cursor: str>` - Get products paginated using cursor. Next and previous page `cursors` provided in responses.
- [GET] `/products/(int: product_id)` - Get product with product_id
- [GET] `/products/(int: product_id)/subcategories` - Get subcategories related to product_id
- [DELETE] `/products/(int: product_id)` (Protected) - Delete product with product_id

- [POST] `/products` (Protected) - Create a new product
  ```
  {
    "name": "name",
    "description": "description",
    "subcategories": [<subcategory ids>] //optional
  }
  ```

- [PUT] `/products/(int: product_id)` (Protected) - Update product with product_id
  ```
  {
    "name": "name",
    "description": "description",
    "subcategories": [<subcategory ids>] //optional
  }
  ```
