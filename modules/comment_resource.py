import datetime

from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify, request
from werkzeug.security import check_password_hash

from . import db_session
from .comment import Comment
from .news import News
from .user import User
from .comment_parser import parser


def abort_if_comment_not_found(com_id):
    session = db_session.create_session()
    com = session.query(Comment).get(com_id)
    if not com:
        abort(404, message=f"Comment with id {com_id} not found")


class CommentResource(Resource):
    def get(self, com_id):
        abort_if_comment_not_found(com_id)
        session = db_session.create_session()
        com = session.query(Comment).get(com_id)
        return jsonify({'comment': com.to_dict(
            only=('id', 'text', 'news.id', 'creator_id'))})

    def delete(self, com_id):
        abort_if_comment_not_found(com_id)

        creator_data = request.json

        session = db_session.create_session()
        com = session.query(Comment).get(com_id)

        if creator_data.get('creator_password') is None:
            abort(405, message=f'to delete comment by user with id >{com.creator_id}<'
                               f' send his password in json with "creator_password" key. '
                               f'Exception at comment with id {com.id}')

        creator = session.query(User).get(com.creator_id)

        if not check_password_hash(creator.hashed_password, creator_data['creator_password']):
            return abort(405, message=f"password doesn't match comment creator password, "
                                      f"can't delete comment with id {com.id}")

        session.delete(com)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, com_id):
        abort_if_comment_not_found(com_id)

        # if there's no json error 400 pops and there is no way to control it...
        args = request.json
        for key in ['text', 'creator_password']:
            args[key] = args.get(key, None)

        session = db_session.create_session()

        comment = session.query(Comment).get(com_id)

        if args['creator_password'] is None:
            abort(405, message=f"you need user password to change one of his comments. Json key is 'creator_password'. "
                               f"Exeption at comment with id {com_id}")

        if args['text'] is None:
            abort(405, message=f"Exeption at comment with id {com_id}. There's literally only one option you can "
                               f"change - 'text' (json key). Please don't mess up here...")

        creator = session.query(User).get(comment.creator_id)

        if not check_password_hash(creator.hashed_password, args['creator_password']):
            abort(405, message=f"user password doesn't match with sent one."
                               f"Exception at comment with id {com_id}")

        comment.text = args['text']
        comment.creation_date = datetime.datetime.now()
        comment.is_edited = True

        session.commit()
        return jsonify({'success': 'OK'})


class CommentListResource(Resource):
    def get(self):
        session = db_session.create_session()
        comms = session.query(Comment).all()
        return jsonify({'comments': [item.to_dict(
            only=('id', 'text', 'news.id', 'creator_id')) for item in comms]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()

        user = session.query(User).get(args['creator_id'])
        news = session.query(News).get(args['news_id'])

        if not news:
            abort(404, message=f'News with id {args["news_id"]} not found')

        if not user:
            abort(404, message=f'User with id {args["creator_id"]} not found')

        if not check_password_hash(user.hashed_password, args['creator_password']):
            abort(405, message=f"user password doesn't match with sent one. Can't create comment by invalid user")

        comment = Comment(
            text=args['text'],
            creator_id=args['creator_id']
        )
        news.comments.append(comment)

        session.add(comment)
        session.commit()
        return jsonify({'success': 'OK'})
