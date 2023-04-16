import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class News(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'news'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    images = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='')

    tags = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    creation_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    creator = orm.relationship('User')

    comments = orm.relationship("Comment", back_populates='news')
