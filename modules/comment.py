import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Comment(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    creation_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    is_edited = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    creator_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    news_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("news.id"))
    news = orm.relationship('News')
