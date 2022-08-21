import os
from flask import flash, render_template, redirect, url_for, current_app
from app import db
from sqlalchemy import func
from app.models import Transaction, BankAccount, UploadMap
from app.upload.forms import CSVForm, UploadProcessingForm
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import json
from app.upload import bp

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file(filename, bankAccountID):
    account = BankAccount.query.get(bankAccountID)
    uploadMap = account.upload_map[0]
    df = pd.read_csv(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', filename))
    for row in df.index:
        # Add filter for users.
        if not Transaction.query.filter_by(transaction_id=df.iloc[row][uploadMap.transaction_id]).first():
            transactionId = "".join(df.iloc[row][uploadMap.transaction_id].split(','))
            postDate = datetime.strptime(df.iloc[row][uploadMap.post_date], uploadMap.date_format).date()
            transactionType = df.iloc[row][uploadMap.transaction_type]
            amount = float(df.iloc[row][uploadMap.amount])
            description = " ".join(df.iloc[row][uploadMap.description].split())
            transaction = Transaction(transaction_id=transactionId, post_date=postDate, transaction_type=transactionType, amount=amount, description=description, bank_account=account)
            db.session.add(transaction)
            db.session.commit()

def csv_file_columns():
    files = os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions'))
    df = pd.read_csv(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', files[0]))
    return df.columns

@bp.route('/transactions', methods=['GET', 'POST'])
def upload():

    form = CSVForm()
    form.bankName.choices = [(b.name_bank, b.name_bank) for b in BankAccount.query.order_by('name_bank')]
    form.accountName.choices = [(a.name_account, a.name_account) for a in BankAccount.query.order_by('name_account')]

    if form.validate_on_submit():
        stmt = db.select(BankAccount).where(BankAccount.name_bank == form.bankName.data).where(BankAccount.name_account == form.accountName.data)
        bankAccount = db.session.scalars(stmt).one()

        f = form.upload.data
        filename = secure_filename(f.filename)
        # Probably should create a short GUID folder for each user.
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', filename))

        if len(bankAccount.upload_map) > 0:
            process_file(filename, bankAccount.id)
            if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', filename)):
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', filename))
            flash('New transactions have been processed!')
            return redirect(url_for('main.transactions_assign'))
        else:
            return redirect(url_for('upload.define_upload_processing', bank_id=bankAccount.id))
    return render_template('upload/upload.html', title='Upload Transactions', form=form)

@bp.route('/transactions/define_processing/<bank_id>', methods=['GET', 'POST'])
def define_upload_processing(bank_id):
    form = UploadProcessingForm()
    fcolumns = csv_file_columns()
    headings = []
    for heading in fcolumns:
        headings.append((heading, heading))

    form.transactionId.choices = headings
    form.postDate.choices = headings
    form.transactionType.choices = headings
    form.amount.choices = headings
    form.description.choices = headings

    if form.validate_on_submit():
        bank = BankAccount.query.get(bank_id)
        uploadmap = UploadMap(transaction_id=form.transactionId.data, post_date=form.postDate.data, transaction_type=form.transactionType.data, \
            amount=form.amount.data, description=form.description.data, date_format=form.dateFormat.data, bank_account=bank)

        db.session.add(uploadmap)
        db.session.commit()
        flash("Upload map added!")
        filename = os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions'))[0]
        process_file(filename, bank_id)
        if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', filename)):
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], 'transactions', filename))
        flash('New transactions have been processed!')
        return redirect(url_for('main.transactions_assign'))
    return render_template('upload/define_upload_processing.html', title='Define Upload Processing', form=form)