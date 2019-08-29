from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    OS = db.Column(db.String(140))
    hostname = db.Column(db.String(140))
    username = db.Column(db.String(140))
    version = db.Column(db.String(140))
    language = db.Column(db.String(140))
    UUID = db.Column(db.String(140))
    current_time = db.Column(db.String(140))
    timezone = db.Column(db.String(140))
    boot_time = db.Column(db.String(140))
    domain = db.Column(db.String(140))
    workgroup = db.Column(db.String(140))
    machineinfo = db.Column(db.JSON)
    tasks = db.relationship('Task', backref='sensor', lazy='dynamic')


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64))
    cmd = db.Column(db.String(64))
    time_result = db.Column(db.DateTime)
    data = db.Column(db.Binary)
    status = db.Column(db.String(14))
    flag_wait_result = db.Column(db.Boolean)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable = False)