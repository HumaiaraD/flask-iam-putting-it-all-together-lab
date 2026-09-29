#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

class Signup(Resource):
    def post(self):
        data= request.get_json() or {}

        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return {'error': 'Username and passsword are required'}, 422
        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists'}, 422

        user = User(username=username, image_url=image_url, bio=bio)
        user.password_hash = password

        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }, 201


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id is not None:
            user = User.query.filter(User.id == session['user_id']).first()
            if user is not None:
                return UserSchema().dump(user), 200

        return {"error": "Unauthorized"}, 401

class Login(Resource):
    def post(self):
        data = request.get_json() or {}

        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        return {'error': 'Invalid username or password'}, 401


class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return (), 204
        return {}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id is None:
            return {"error": "Unauthorized"}, 401

        recipes = Recipe.query.all()
        body = RecipeSchema(many=True).dump(recipes)
        return make_response(body, 200)

    def post(self):
        user_id = session.get('user_id')
        if user_id is None:
            return {"error": "Unauthorized"}, 401

        try:
            data = RecipeSchema().load(request.get_json()) or {}
            r = Recipe(**data, user_id=user_id)
            db.session.add(r)
            db.session.commit()
            
            return make_response(RecipeSchema().dump(r), 201)
        except (ValidationError, ValueError, IntegrityError):
            db.session.rollback()
            return {'errors': 'Invalid recipe data'}, 422


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)