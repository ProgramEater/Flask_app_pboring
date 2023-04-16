from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify, request
from werkzeug.security import check_password_hash

from . import db_session
from .user import User
from .comment import Comment
from .user_parser import parser


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    users = session.query(User).get(user_id)
    if not users:
        abort(404, message=f"User with id {user_id} not found")


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'users': user.to_dict(
            only=('nickname', 'email', 'about', 'id'))})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)

        user_data = request.json

        if user_data.get('password', None) is None:
            return abort(405, message=f'to delete user with id {user_id} send his password in json with "password" key')

        session = db_session.create_session()
        user = session.query(User).get(user_id)

        if not check_password_hash(user.hashed_password, user_data['password']):
            return abort(405, message=f"password doesn't match user password, can't delete user with id {user_id}")

        user_comments = session.query(Comment).filter(Comment.creator_id == user.id)
        for com in user_comments:
            session.delete(com)
        session.commit()

        for news in user.news:
            news.creator_id = 1
        session.commit()

        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        abort_if_user_not_found(user_id)

        session = db_session.create_session()
        user = session.query(User).get(user_id)

        args = parser.parse_args()

        new_password = request.json.get('new_password', None)

        if not check_password_hash(user.hashed_password, args['password']):
            abort(405, message=f"Password for user (id={user_id}) you're trying to change is not correct")

        user_e = session.query(User).filter(User.email == args['email']).first()
        if user_e is not None and user_e != user:
            abort(405, message=f"User with the email {args['email']} already exists (not you)")

        user.nickname = args['nickname']
        user.about = args['about'] if args['about'] is not None else user.about
        user.email = args['email']
        if new_password is not None:
            user.set_password(new_password)

        session.commit()
        return jsonify({'success': 'OK', 'tip': 'send news password with key "new_password" '
                                                'in json in order to change password'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'nickname', 'email')) for item in users]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()

        user_e = session.query(User).filter(User.email == args['email']).first()
        if user_e:
            abort(405, message=f'User with email {args["email"]} already exists')

        print(args['about'])

        user = User(
            nickname=args['nickname'],
            about=args['about'] if args['about'] is not None else '',
            email=args['email']
        )
        user.set_password(args['password'])

        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})
