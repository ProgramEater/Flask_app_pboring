from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify, request
from werkzeug.security import check_password_hash

from . import db_session
from .news import News
from .user import User
from .news_parser import parser


def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(News).get(news_id)
    if not news:
        abort(404, message=f"News with id {news_id} not found")


class NewsResource(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        return jsonify({'news': news.to_dict(
            only=('id', 'title', 'about', 'creator.nickname', 'tags'))})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)

        creator_data = request.json
        session = db_session.create_session()
        news = session.query(News).get(news_id)

        if news.creator.id == 1:
            abort(405, message=f"can't delete news (id={news_id}), belongs to deleted user")

        if creator_data.get('creator_password') is None:
            abort(405, message=f'to delete news created by user with {news.creator.id} id'
                               f' send his password in json with "creator_password" key. '
                               f'Exception at news with id {news_id}')

        if not check_password_hash(news.creator.hashed_password, creator_data['creator_password']):
            return abort(405, message=f"password doesn't match news creator password, "
                                      f"can't delete news with id {news_id}")

        for com in news.comments:
            session.delete(com)
        session.commit()

        session.delete(news)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, news_id):
        abort_if_news_not_found(news_id)

        # if there's no json error 400 pops and there is no way to control it...
        args = request.json
        for key in ['title', 'about', 'tags', 'creator_password']:
            args[key] = args.get(key, None)

        session = db_session.create_session()

        news = session.query(News).get(news_id)

        if args['creator_password'] is None:
            abort(405, message=f"you need user password to change one of his news. Json key is 'creator_password'. "
                               f"Exeption at news with id {news_id}")

        if news.creator.hashed_password is None:
            abort(405, message=f"can't change this user news (deleted user)")

        if not check_password_hash(news.creator.hashed_password, args['creator_password']):
            abort(405, message=f"user password doesn't match with sent one."
                               f"Exception at news with id {news_id}")

        if args['tags'] is not None and args['tags'][0] != '#':
            abort(405, message=f'news tags should start with "#" like that: #tag1 #tag2. '
                               f'Exception at news with id {news_id}')

        news.title = args['title'] if args['title'] is not None else news.title
        news.about = args['about'] if args['about'] is not None else news.about
        news.tags = ';'.join(f' {args["tags"]}'.split(' #'))[1:] if args['tags'] is not None else news.tags

        session.commit()
        return jsonify({'success': 'OK'})


class NewsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        news = session.query(News).all()
        return jsonify({'news': [item.to_dict(
            only=('id', 'title', 'about', 'creator.nickname', 'tags')) for item in news]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()

        user = session.query(User).get(args['creator_id'])

        if user is None:
            abort(404, message=f'User with id {args["creator_id"]} not found')

        if args['creator_id'] == 1:
            abort(405, message=f"can't change this user news (deleted user)")

        if check_password_hash(user.hashed_password, args['creator_password']):
            abort(405, message=f"user password doesn't match with sent one. Can't create news by invalid user")

        if args['tags'] is not None and args['tags'][0] != '#':
            abort(405, message=f'news tags should start with "#" like that: #tag1 #tag2.')

        news = News(
            title=args['title'],
            about=args['about'],
            tags=';'.join(f' {args["tags"]}'.split(' #'))[1:] if args['tags'] is not None else '',
            creator_id=args['creator_id']
        )

        session.add(news)
        session.commit()
        return jsonify({'success': 'OK'})
