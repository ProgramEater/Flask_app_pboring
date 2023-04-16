from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('text', required=True)
parser.add_argument('creator_id', required=True, type=int)
parser.add_argument('creator_password', required=True)
parser.add_argument('news_id', required=True, type=int)
