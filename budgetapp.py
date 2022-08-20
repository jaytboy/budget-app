from app import app, db
from app.models import CategoryGroup, Category, Transaction,  CategoryAmount, BankAccount, UploadMap, MonthlyBudget
from datetime import datetime

@app.shell_context_processor
def make_shell_context():
	return {'datetime': datetime, 'db': db, 'CategoryGroup': CategoryGroup, 'Category': Category, 'Transaction': Transaction, 'CategoryAmount': CategoryAmount, 'BankAccount': BankAccount, 'UploadMap': UploadMap, 'MonthlyBudget': MonthlyBudget}