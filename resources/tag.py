from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

blp = Blueprint('Tags', __name__, description='Operations on tags')


@blp.route('/store/<int:store_id>/tag')
class TagsInStore(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        tag_name = tag_data.get('name')
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_name).first():
            abort(400, message=f'tag name: {tag_name} already exist in store_id: {store_id}')

        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
            return tag
        except SQLAlchemyError:
            abort(500, message=f'error occurred while creating tag: {tag_name}')


@blp.route('/item/<int:item_id>/tag/<int:tag_id>')
class LinkTagsToItem(MethodView):
    @jwt_required()
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        item.tags.append(tag)
        try:
            db.session.add(item)
            db.session.commit()
            return tag
        except SQLAlchemyError:
            abort(500, message=f'error occurred while linking tag_id: {tag_id} to item_id: {item_id}')

    @jwt_required()
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        item.tags.remove(tag)
        try:
            db.session.add(item)
            db.session.commit()
            return {
                'message': f'tag_id: {tag_id} is unlink to item_id: {item_id}'
            }
        except SQLAlchemyError:
            abort(500, message=f'error occurred while unlinking tag_id: {tag_id} to item_id: {item_id}')


@blp.route('/tag/<int:tag_id>')
class Tag(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @jwt_required()
    @blp.response(
        202,
        description='Deletes an empty tag',
        example={'message': 'tag_id: 1 is deleted'},
    )
    @blp.alt_response(404, description='tag_id does not exist')
    @blp.alt_response(400, description='tag is not empty')
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {'message': f'tag_id: {tag_id} has been deleted'}

        abort(400, message=f'error occurred while deleting tag_id: {tag_id}')
