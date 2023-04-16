from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('about', required=True)
parser.add_argument('tags', required=False)
parser.add_argument('creator_id', required=True, type=int)
parser.add_argument('creator_password', required=True)
