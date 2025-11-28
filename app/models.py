from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    dni = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(64))
    city = db.Column(db.String(64))
    photo = db.Column(db.String(128)) # Filename
    bio = db.Column(db.String(256))
    coins = db.Column(db.Integer, default=100)
    
    products = db.relationship('Product', backref='owner', lazy='dynamic')
    # Trades where user is the proposer
    trades_proposed = db.relationship('Trade', foreign_keys='Trade.proposer_id', backref='proposer', lazy='dynamic')
    # Trades where user is the receiver (owner of the product being requested)
    trades_received = db.relationship('Trade', foreign_keys='Trade.receiver_id', backref='receiver', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    description = db.Column(db.String(500))
    category = db.Column(db.String(64))
    condition = db.Column(db.String(64))
    photos = db.Column(db.String(500)) # Comma separated filenames
    status = db.Column(db.String(20), default='active') # active, traded, deleted
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    
    status = db.Column(db.String(20), default='pending') # pending, accepted, completed, cancelled
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    proposer_confirmed_at = db.Column(db.DateTime)
    receiver_confirmed_at = db.Column(db.DateTime)
    chat_active = db.Column(db.Boolean, default=True)  # Track if conversation is ongoing
    
    product = db.relationship('Product', backref='trades')
    messages = db.relationship('Message', backref='trade', lazy='dynamic')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', backref='messages')
