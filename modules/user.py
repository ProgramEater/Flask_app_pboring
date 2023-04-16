import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    nickname = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    about = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='')

    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)

    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    # path to the profile picture
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True, default='no_pfp.png')

    news = orm.relationship("News", back_populates='creator')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
