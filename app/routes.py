from flask import request, abort, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from email_validator import EmailNotValidError

from app import app, db
from app.models import User


@app.route('/auth/register', methods=['POST'])
def register():
    """
    Register a new user.
    ---
    tags:
        - User
    description: Register a new user.
    requestBody:
        required: true
        description: email - Email id <br> password - Password
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - email
                        - password
                    properties:
                        email:
                            type: string
                        password:
                            type: string
    responses:
        201:
            description: User registered successfully.
        400:
            description: Invalid input.
        409:
            description: Email already exists.
        500:
            description: Internal Server Error.
    """
    if not request.json:
        abort(400)

    try:
        email = request.json.get('email')
        password = request.json.get('password')
        if not email or not password:
            abort(400)

        user = User()
        user.set_email(email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return { "message": "Registered!" }, 201
    except IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409
    except EmailNotValidError as e:
        return jsonify(code='invalid_email_format', error=str(e)), 400


@app.route('/auth/login', methods=['POST'])
def login():
    """
    Login a user.
    ---
    tags:
        - User
    description: Login a user.
    requestBody:
        required: true
        description: email - Email id <br> password - Password
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - email
                        - password
                    properties:
                        email:
                            type: string
                        password:
                            type: string
    responses:
        200:
            description: User logged in successfully.
        400:
            description: Invalid input.
        401:
            description: Invalid username or password.
        500:
            description: Internal Server Error.
    """
    if not request.json:
        abort(400)

    email = request.json.get('email')
    password = request.json.get('password')
    if not email or not password:
        abort(400)

    user = User.get(email=email)
    if not user or not user.check_password(password):
        return jsonify(error='Invalid username or password. Check again or register.'), 401

    access_token = create_access_token(identity=str(user.id), fresh=True)
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200


@app.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Get new access token using your refresh token
    ---
    tags:
        - User
    description: Get new access token using your refresh token.
    security:
        - refresh_token: []
    responses:
        200:
            description: New access token.
        401:
            description: Token expired, missing or invalid.
        500:
            description: Internal Server Error.
    """
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify(access_token=access_token), 200
