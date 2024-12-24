<h1>Ecommerce REST API</h1>
RESTful HTTP API using Python Flask that allows users to manage their ecommerce platform.
<br></br>
Ability to create, read, update, and delete products, categories and subcategories. A category can have multiple subcategories and a subcategory can belong to multiple categories. Products can belong to multiple categories and subcategories.
<br></br>
Fetching a product fetches the details of categories and subcategories it belongs to. Provides the ability to search for products by name, category and subcategories.
<br></br>
Paginates result when products are fetched by categories or subcategories. 

### Requirements
This project is written in `Python 3.12.1`

```bash
pip install -r requirements.txt
```
`requirements.txt` contains an adapter for PostgreSQL by default.

### Usage

Copy `.env.example` and rename to `.env`. Provide your database URL to the `SQLALCHEMY_DATABASE_URI` environment variable.

Create database tables:

```bash
flask --app app shell
>>> with app.app_context():
>>>     db.create_all()
```

Start the server: (Runs on 127.0.0.1:5000)

```bash
flask --app app run [--debug]
``` 

Test the API using Postman, cURL or your preferred HTTP client.

### Endpoints

#### Fetch products using name, category, subcategory
- [GET] `/product/<name: string>` - Get product with name: `name`
<br></br>
- [GET] `/subcategory/<subcategory_id: int>/products` - Get product with within subcategory `subcategory`. Returns first page of the paginated results.
<br></br>
- [GET] `/subcategory/<subcategory_id: int>/products?page=<page_no>` - Get product with within subcategory `subcategory`. Returns `page_no` of the paginated results.
<br></br>
- [GET] `/category/<category_id: int>/products` - Get product with within category `category`. Returns first page of the paginated results.
<br></br>
- [GET] `/category/<category_id: int>/products?page=<page_no>` - Get product with within category `category`. Returns `page_no` of the paginated results.

<br></br>
#### Category
- [GET] `/categories` - Get all categories
- [GET] `/category/(int: category_id)` - Get category with category_id
- [DELETE] `/category/(int: category_id)` - Delete category with category_id

- [POST] `/category/create` - Create a new category
```
{
  "name": "name",
  "subcategories": [<subcategory ids>] //optional
}
```

- [PUT] `/category/(int: category_id)/update` - Update category with category_id
```
{
  "name": "name",
  "subcategories": [<subcategory ids>] //optional
}
```

<br></br>
#### Subcategory
- [GET] `/subcategories` - Get all subcategories
- [GET] `/subcategory/(int: subcategory_id)` - Get subcategory with subcategory_id
- [DELETE] `/subcategory/(int: subcategory_id)` - Delete subcategory with subcategory_id

- [POST] `/subcategory/create` - Create a new subcategory
```
{
  "name": "name",
  "categories": [(category ids)] //optional
  "products": [<subcategory ids>] // optional
}
```

- [PUT] `/subcategory/(int: subcategory_id)/update` - Update subcategory with subcategory_id
```
{
  "name": "name",
  "categories": [<category ids>] //optional
  "products": [<subcategory ids>] // optional
}
```


<br></br>
#### Product
- [GET] `/products` - Get all products
- [GET] `/product/(int: product_id)` - Get product with product_id
- [DELETE] `/product/(int: product_id)` - Delete product with product_id

- [POST] `/product/create` - Create a new product
```
{
  "name": "name",
  "description": "description",
  "subcategories": [<subcategory ids>] //optional
}
```

- [PUT] `/product/(int: product_id)/update` - Update product with product_id
```
{
  "name": "name",
  "description": "description",
  "subcategories": [<subcategory ids>] //optional
}
```
