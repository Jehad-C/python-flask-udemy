from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import UserSchema

blp = Blueprint('Users', __name__, description='Operations on users')


@blp.route('/user/<int:user_id>')
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {'message': f'user_id: {user_id} has been deleted'}


@blp.route('/register')
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    @blp.response(
        201,
        description='Register a user',
        example={'message': 'username: 1 has been created'}
    )
    def post(self, user_data):
        username = user_data['username']
        if UserModel.query.filter(UserModel.username == username).first():
            abort(400, message=f'user name: {username} already exist')

        user = UserModel(
            username=username,
            password=pbkdf2_sha256.hash(user_data['password'])
        )

        db.session.add(user)
        db.session.commit()
        return {'message': f'user {username} has beem created'}


@blp.route('/login')
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data['username']
        ).first()

        if user and pbkdf2_sha256.verify(user_data['password'], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            return {'access_token': access_token, 'refresh_token': refresh_token}

        abort(401, f'username or password is incorrect')


@blp.route('/logout')
class UserLogout(MethodView):

    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLOCKLIST.add(jti)
        return {'message': 'user has been logout'}


@blp.route('/refresh')
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        user = get_jwt_identity()
        token = create_access_token(identity=user, fresh=False)
        return {'access_token': token}
