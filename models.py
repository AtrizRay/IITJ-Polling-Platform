from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, JSON
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model representing the users of the application."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # e.g., 'master_admin', 'local_admin', 'student'
    institute_id = db.Column(db.String(50), nullable=True)  # Changed to String to match app.py
    voted_poll_ids = db.Column(db.JSON, default=list)  # Store IDs of polls user has voted on

    def __repr__(self):
        return f'<User {self.username}>'

class Option(db.Model):
    """Option model representing the options for each poll."""
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)

    poll = db.relationship('Poll', backref='poll_options')  # Changed backref name to avoid conflicts

    def __repr__(self):
        return f'<Option {self.text}>'

class Poll(db.Model):
    __tablename__ = 'polls'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    institute_id = db.Column(db.String(50), nullable=False)
    institute = db.Column(db.String(100), nullable=False)
    option_texts = db.Column(db.Text, nullable=False)  # Stores comma-separated options
    responses = db.Column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, question, institute_id, institute=None, responses=None):
        self.question = question
        self.institute_id = institute_id
        self.institute = institute or f'Institute {institute_id}'
        self.option_texts = ""
        self.responses = responses or {}
        self.active = True

    def set_options(self, options_list):
        """Set options as a comma-separated string"""
        if isinstance(options_list, list):
            self.option_texts = ','.join(str(opt).strip() for opt in options_list)
        elif isinstance(options_list, str):
            self.option_texts = options_list

    def get_options(self):
        """Get options as a list"""
        if not self.option_texts:
            return []
        return [opt.strip() for opt in self.option_texts.split(',') if opt.strip()]

    @property
    def options(self):
        """Property to access options as a list"""
        return self.get_options()

class Vote(db.Model):
    """Vote model representing the votes cast by users on polls."""
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)

    user = db.relationship('User', backref='votes')
    poll = db.relationship('Poll', backref='votes')

    def __repr__(self):
        return f'<Vote user_id={self.user_id}, poll_id={self.poll_id}>'