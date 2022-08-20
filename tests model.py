from app import db
from datetime import date

# TODO
# --
# FIX ERROR in db upgrade!!!!!!!!!!!!!

# class User(db.Model):
#   id = db.Column(db.Integer, primary_key=True)
#   username = db.Column(db.String(64), index=True, unique=True)
#     email = db.Column(db.String(120), index=True, unique=True)
#     password_hash = db.Column(db.String(128))

# class MonthlyBudget(db.Model):
#   id = db.Column(db.Integer, primary_key=True)
#   amount = db.Column(db.Float, nullable=False)
#   date = db.Column(db.Date, nullable=False)
#   # Relationships
#   id_category = db.Column(db.Integer, db.ForeignKey('category.id'))
#   # id_user = db.Column(db.Integer, db.ForeignKey('user.id'))

# class CategoryAutoassign(db.Model):
#   id = db.Column(db.Integer, primary_key=True)
#   description = description = db.Column(db.String(140))
#   # Relationships
#   id_category = db.Column(db.Integer, db.ForeignKey('category.id'))
#   # id_user = db.Column(db.Integer, db.ForeignKey('user.id'))