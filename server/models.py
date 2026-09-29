from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields  # type: ignore[import-not-found]

from config import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    #relationship
    recipes = db.relationship("Recipe", back_populates="user")

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8')
        )
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8')
        )

    def __repr__(self):
        return f"<User {self.username}, {self.image_url}, {self.bio}>"

class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)

    #relationship
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="recipes")

    # validations for constraints
    @validates("title")
    def validate_title(self, key, value):
        if not value or not value.strip():
            raise ValueError("Title is required")
        return value

    @validates("instructions")
    def validate_instructions(self, key, value):
        if not value or len(value.strip()) < 50:
            raise ValueError("Instructions must be atleast 50 characters long.")
        return value

    def __repr__(self):
        return f"<Recipe {self.id}: {self.title}>"

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.String()
    #_password_hash = fields.String()
    image_url = fields.String()
    bio = fields.String()

    recipes = fields.Nested(lambda: RecipeSchema(exclude=("user",)), many=True)

class RecipeSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.String()
    instructions = fields.String()
    minutes_to_complete = fields.Int()

    user = fields.Nested(lambda: UserSchema(exclude=('recipes',)))