from flask_wtf import FlaskForm
from app.models import Category, BankAccount
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField, SubmitField, HiddenField, FormField, FieldList, DecimalField
from wtforms.validators import DataRequired, Length
from werkzeug.utils import secure_filename

cat1 = [('-', '-')]

for c in Category.query.order_by('id'):
        cat1.append((str(c.id), c.category))


cat2 = [('-', '-'), ('split', 'Split')]

for c in Category.query.order_by('id'):
        cat2.append((str(c.id), c.category))


class CSVForm(FlaskForm):
	bankName = SelectField('Bank Name')
	accountName = SelectField('Account Name')
	upload = FileField('csv file', validators=[
		FileRequired(), 
		FileAllowed(['csv'], 'CSV files only!')
	])
	submit = SubmitField('Upload')

class UploadProcessingForm(FlaskForm):
	transactionId = SelectField('Transaction ID')
	postDate = SelectField('Post Date')
	dateFormat = SelectField('Date Format', choices=[("%m/%d/%Y","%m/%d/%Y (01/31/1970)")])
	transactionType = SelectField('Transaction Type (eg. Check, Credit, Debit)')
	amount = SelectField('Amount')
	description = SelectField('Description')
	submit = SubmitField('Process')

def category_selected(form, field):
	if field.data == '-':
		raise ValidationError('Category must be selected')

class AssignCatergoryForm(FlaskForm):
	transactionId = StringField('', validators=[DataRequired(), Length(max=64)])
	category = SelectField('Category', choices=cat2, validators=[DataRequired(), category_selected])
	submit = SubmitField('Assign Category')

class AddCategoryGroupForm(FlaskForm):
	group = StringField('Category Group', validators=[DataRequired()])
	submit = SubmitField('Add Category Group')

class AddCategoryForm(FlaskForm):
	group = SelectField('Category Group', coerce=int)
	category = StringField('Category', validators=[DataRequired()])
	submit = SubmitField('Add Category')

class CategoryAmountForm(FlaskForm):
	# Consider changing to DecimalFeild
	amount = StringField('Amount')
	category = SelectField('Category', choices=cat1)
	
class CategoriesAmountsForm(FlaskForm):
	assignment = FieldList(FormField(CategoryAmountForm), min_entries=5)
	submit = SubmitField('Submit')

class AddBankAccountForm(FlaskForm):
	bankName = StringField('Bank Name', validators=[DataRequired(), Length(max=64)])
	accountName = StringField('Account Name', validators=[Length(max=64)])
	accountNumber = StringField('Last 4 digits of account number', validators=[Length(max=4)])
	submit = SubmitField('Submit')

class BudgetForm(FlaskForm):
	pass

for c in Category.query.order_by('id'):
	setattr(BudgetForm, c.category, StringField(c.category))
	
	