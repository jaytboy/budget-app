from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length
from werkzeug.utils import secure_filename

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