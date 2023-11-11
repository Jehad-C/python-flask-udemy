import uuid
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import StoreModel
from schemas import StoreSchema

blp = Blueprint('stores', __name__, description='Operations on stores')


@blp.route('/store/<int:store_id>')
class Store(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        try:
            store = StoreModel.query.get_or_404(store_id)
            return store
        except KeyError:
            abort(404, message=f'store_id: {store_id} does not exist')

    @jwt_required()
    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {'message': f'store_id: {store_id} has been deleted'}


@blp.route('/store')
class StoreList(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @jwt_required(refresh=True)
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store_name = store_data.get('name')
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
            return store
        except IntegrityError:
            abort(
                400,
                message= f'store name: {store_name} already exist'
            )
        except SQLAlchemyError:
            abort(
                500,
                message=f'error occurred while creating store: {store_name}'
            )
