from app import db
from datetime import date

# Be sure to add all the "nullable=False", "index=True", and "unique=True" where applicable then init a new database

# Parent
class CategoryGroup(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	group = db.Column(db.String(64))

	categories = db.relationship('Category', back_populates='group')

	def __repr__(self):
		return f"<Category Group: group={self.group!r}>"

# Child of CategoryGroup
class Category(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	category = db.Column(db.String(64))
	group_id = db.Column(db.Integer, db.ForeignKey('category_group.id'))

	group = db.relationship('CategoryGroup', back_populates='categories')
	amounts = db.relationship('CategoryAmount', back_populates='category')
	monthly_budgets = db.relationship("MonthlyBudget", back_populates="category")

	def __repr__(self):
		return f"<Category: category={self.category!r}>"

# t = Transaction(transaction_id="62022033120303248000020220331535391163", post_date="2/17/2022".strptime(d,'%m/%d/%Y').date(), transaction_type="Debit", amount="-91.67000", description="Purchase DELTA,1030 DELTA BLVD ATLANTA GAUS")
# Parent
class Transaction(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	transaction_id = db.Column(db.String(64))
	post_date = db.Column(db.Date)
	transaction_type = db.Column(db.String(16))
	amount = db.Column(db.Float)
	description = db.Column(db.String(140))
	bank_account_id = db.Column(db.Integer, db.ForeignKey("bank_account.id"))

	amounts = db.relationship("CategoryAmount", back_populates="transaction", cascade="all, delete-orphan")
	bank_account = db.relationship("BankAccount", back_populates="transactions")

	def __repr__(self):
		return f"<Transaction: id={self.transaction_id!r}, post_date={self.post_date!r}, transaction_type={self.transaction_type!r}, amount={self.amount!r}, description={self.description!r}>"

# Child of Transaction
class CategoryAmount(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	amount = db.Column(db.Float)
	transaction_id=db.Column(db.Integer, db.ForeignKey('transaction.id'))
	category_id=db.Column(db.Integer, db.ForeignKey('category.id'))

	transaction = db.relationship("Transaction", back_populates="amounts")
	category = db.relationship("Category", back_populates="amounts")

	def __repr__(self):
		return f"<CategoryAmount: amount={self.amount!r}, transaction_id={self.transaction_id!r}, category_id={self.category_id!r}>"

# Parent of Transaction and UploadMap
class BankAccount(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name_bank = db.Column(db.String(64))
	name_account = db.Column(db.String(64))
	account_number = db.Column(db.String(4)) #Only allow input of last 4 digits

	transactions = db.relationship("Transaction", back_populates="bank_account", cascade="all, delete-orphan")
	upload_map = db.relationship("UploadMap", back_populates="bank_account", cascade="all, delete-orphan")

	def __repr__(self):
		return f"<BankAccount: name_bank={self.name_bank!r}, name_account={self.name_account!r}, account_number={self.account_number!r}>"

# child of bank_account
class UploadMap(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	transaction_id = db.Column(db.String(64))
	post_date = db.Column(db.String(64))
	transaction_type = db.Column(db.String(64))
	amount = db.Column(db.String(64))
	description = db.Column(db.String(64))
	date_format = db.Column(db.String(32))
	bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'))

	bank_account = db.relationship("BankAccount", back_populates="upload_map")

	def __repr__(self):
		return f"<UploadMap: transaction_id={self.transaction_id!r}, post_date={self.post_date!r}, date_format={self.date_format}, transaction_type={self.transaction_type!r}, amount={self.amount!r}, description={self.description!r}, bank_account_id={self.bank_account_id!r}>"

# Child of category
class MonthlyBudget(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	amount = db.Column(db.Float, nullable=False)
	date = db.Column(db.Date, nullable=False)
	category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

	category = db.relationship("Category", back_populates="monthly_budgets")

	def __repr__(self):
		return f"<MonthlyBudget: amount={self.amount!r}, date={self.date!r}, category={self.category.category!r}>"