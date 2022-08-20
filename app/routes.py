import os
from flask import flash, render_template, request, redirect, url_for
from app import app, db, celery
from sqlalchemy import func
from app.models import CategoryGroup, Category, Transaction, CategoryAmount, BankAccount, UploadMap, MonthlyBudget
from app.forms import CSVForm, AddCategoryForm, AddCategoryGroupForm, AssignCatergoryForm, CategoryAmountForm, CategoriesAmountsForm, AddBankAccountForm, UploadProcessingForm, BudgetForm
from werkzeug.utils import secure_filename
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import json

# TODO:
# - Error checking of validating

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#@celery.task
def process_file(filename, bankAccountID):
    account = BankAccount.query.get(bankAccountID)
    uploadMap = account.upload_map[0]
    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', filename))
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
    files = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions'))
    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', files[0]))
    return df.columns


@app.route('/')
@app.route('/index')
def index():
    trans = Transaction.query.filter(Transaction.amounts != None).order_by(Transaction.post_date.asc()).all()
    
    years = {}

    for tran in trans:
        years[tran.post_date.year] = []

    for tran in trans:
        [years[tran.post_date.year].append(tran.post_date.strftime('%B')) for tran in trans if tran.post_date.strftime('%B') not in years[tran.post_date.year]]


    return render_template('index.html', title='Home', years=years)

@app.route('/transactions/<year>/<month>')
def transactions(year, month):
    groups = CategoryGroup.query.all()
    cats = Category.query.all()

    stmt = (db.select(CategoryAmount).join(CategoryAmount.transaction).join(CategoryAmount.category).where(Transaction.post_date.contains(f"{year}-{datetime.strptime(month, '%B').strftime('%m')}")))
    catAmounts = db.session.scalars(stmt).all()

    totals = {"group": {},
    "category": {}}

    for g in groups:
        amount = 0
        for a in catAmounts:
            if a.category.group.group == g.group:
                amount += a.amount
        totals["group"][g.group] = amount

    for c in cats:
        amount = 0
        for a in catAmounts:
            if a.category.category == c.category:
                amount += a.amount
        totals["category"][c.category] = amount

    return render_template('transactions.html', title='Transactions', groups=groups, cats=cats, catAmounts=catAmounts, totals=totals)

@app.route('/transactions/assign/<transactionid>', methods=['GET', 'POST'])
def category_split(transactionid):
    form = CategoriesAmountsForm()

    if form.validate_on_submit():
        for field in form.assignment:
            if field.category.data != '-':
                transaction = Transaction.query.filter_by(transaction_id=transactionid).first()
                category = Category.query.get(field.category.data)
                cat_amount = CategoryAmount(amount=float(field.amount.data), transaction=transaction, category=category)
                db.session.add(cat_amount)
                db.session.commit()
        return redirect(url_for('transactions_assign'))

    tran = Transaction.query.filter_by(transaction_id=transactionid).first()
    return render_template('category_split.html', title='Split Category', t=tran, form=form)

@app.route('/transactions/assign', methods=['GET', 'POST'])
def transactions_assign():
    form = AssignCatergoryForm()

    if form.validate_on_submit():
        if form.category.data == 'split':
            return redirect(url_for('category_split', transactionid=form.transactionId.data) )
        else:
            transaction = Transaction.query.filter_by(transaction_id=form.transactionId.data).first()
            cat = Category.query.get(form.category.data)
            cat_amount = CategoryAmount(amount=transaction.amount, transaction=transaction, category=cat)
            db.session.add(cat_amount)
            db.session.commit()
            return redirect(url_for('transactions_assign'))

    trans = Transaction.query.filter(Transaction.amounts == None).order_by(Transaction.post_date.asc()).all()
    return render_template('assign_transactions.html', title='Assign Transactions', form=form, trans=trans)



@app.route('/transactions/upload', methods=['GET', 'POST'])
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
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', filename))

        if len(bankAccount.upload_map) > 0:
            process_file(filename, bankAccount.id)
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', filename)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', filename))
            flash('New transactions have been processed!')
            return redirect(url_for('transactions_assign'))
        else:
            return redirect(url_for('define_upload_processing', bank_id=bankAccount.id))
    return render_template('upload.html', title='Upload Transactions', form=form)

@app.route('/transactions/define_upload_processing/<bank_id>', methods=['GET', 'POST'])
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
        filename = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions'))[0]
        process_file(filename, bank_id)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', filename)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'transactions', filename))
        flash('New transactions have been processed!')
        return redirect(url_for('transactions_assign'))
    return render_template('define_upload_processing.html', title='Define Upload Processing', form=form)

# Need to add ability to edit.
@app.route('/add_category_group', methods=['GET', 'POST'])
def add_category_group():
    form = AddCategoryGroupForm()
    if form.validate_on_submit():
        group = CategoryGroup(group=form.group.data)
        db.session.add(group)
        db.session.commit()
        flash('Group {} added!'.format(form.group.data))
        return redirect(url_for('add_category_group'))
    groups = CategoryGroup.query.order_by(CategoryGroup.group.desc()).all()
    return render_template('add_category_group.html', title='Add Category Group', form=form, groups=groups)    

# Need to add ability to edit.
@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    form = AddCategoryForm()
    form.group.choices = [(g.id, g.group) for g in CategoryGroup.query.order_by('id')]
    if form.validate_on_submit():
        group = CategoryGroup.query.get(form.group.data)
        cat = Category(group=group, category=form.category.data)
        db.session.add(cat)
        db.session.commit()
        flash('Group {} and category {} added!'.format(form.group.data, form.category.data))
        return redirect(url_for('add_category'))
    cats = Category.query.order_by(Category.category.desc()).all()
    return render_template('add_category.html', title='Add Category', form=form, cats=cats)

@app.route('/add_bank_account', methods=['GET', 'POST'])
def add_bank_account():
    form = AddBankAccountForm()
    if form.validate_on_submit():
        bank = BankAccount(name_bank=form.bankName.data, name_account=form.accountName.data, account_number=form.accountNumber.data)
        db.session.add(bank)
        db.session.commit()
        flash(f"{form.accountName.data} account from {form.bankName.data} added!")
        return redirect(url_for('add_bank_account'))
    banks = BankAccount.query.order_by(BankAccount.name_bank.desc()).all()
    return render_template('add_bank_account.html', title='Add Bank Account', form=form, banks=banks)

# Consider adding not to this month
@app.route('/budget/all', methods=['GET', 'POST'])
def budgets():
    datenow = datetime.now().date()
    thismonth = datetime(datenow.year, datenow.month, 1).date()
    twomonthsago = thismonth - relativedelta(months=2)
    # Read about time and servers here: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xii-dates-and-times
    # Seems like a good chance for pagenation or toggel months of a given year.
    
    data = db.session.scalars(db.select(MonthlyBudget.date).order_by(MonthlyBudget.date.asc())).unique().all()
    years = {}
    dates = []
    for date in data:
        years[date.year] = None
        if date < twomonthsago:
            dates.append(("review_budget",date, datetime.strptime(str(date.month), '%m').strftime('%B')))
        else:
            dates.append(("edit_budget",date, datetime.strptime(str(date.month), '%m').strftime('%B')))
    years = list(years)
    datemax = max(data)
    future_date = datemax + relativedelta(months=1)
    future = ("create_budget", future_date, datetime.strptime(str(future_date.month), '%m').strftime('%B'))

    return render_template('budgets.html', title='Budgets', dates=dates, years=years, future=future)

@app.route('/budget/create/<year>/<month>', methods=['GET', 'POST'])
def create_budget(year, month):
    datenow = datetime.now().date()
    thismonth = datetime(datenow.year, datenow.month, 1).date()
    sixmonthsago = thismonth - relativedelta(months=6)

    monthstr = datetime.strptime(month, '%m').strftime('%B')
    forms = BudgetForm()
    groups = CategoryGroup.query.all()
    cats = Category.query.order_by('id').all()
    averageAmount = {}
    for cat in cats:
        amountSum = db.session.query(func.sum(MonthlyBudget.amount)).order_by(MonthlyBudget.date.asc()).filter(MonthlyBudget.date > sixmonthsago). \
        join(Category).filter(Category.category == cat.category).one()[0]
        amountCount = db.session.query(func.count(MonthlyBudget.amount)).order_by(MonthlyBudget.date.asc()).filter(MonthlyBudget.date > sixmonthsago). \
        join(Category).filter(Category.category == cat.category).one()[0]
        
        averageAmount[cat.category] = amountSum/amountCount

    if forms.validate_on_submit():
        budget = []
        for cat in cats:
            budget.append(MonthlyBudget(amount=float(getattr(forms, cat.category).data), date=datetime(int(year),int(month),1).date(), category=cat))
        db.session.add_all(budget)
        db.session.commit()
        flash(f"{monthstr}'s budget created successfully!")
        return redirect(url_for('budgets'))

    return render_template('budget_create.html', title='Create budget for ' + monthstr + ', ' + year, month=monthstr, \
            year=year, groups=groups, forms=forms, cats = cats, averageAmount=averageAmount)
# FIX
@app.route('/budget/edit/<year>/<month>', methods=['GET', 'POST'])
def edit_budget(year, month):
    selectedmonth = datetime(int(year), int(month), 1).date()
    monthstr = datetime.strptime(month, '%m').strftime('%B')
    groups = CategoryGroup.query.all()
    cats = Category.query.order_by('id').all()
    budgetdata = MonthlyBudget.query.filter_by(date=selectedmonth).order_by(MonthlyBudget.category_id.asc()).all()

    forms = BudgetForm()
    budget = {}
    for b in budgetdata:
        budget[b.category.category] = b.amount

    if forms.validate_on_submit():
        i = 0
        for cat in cats:
            if budgetdata[i].amount != float(getattr(forms, cat.category).data):
                budgetdata[i].amount = float(getattr(forms, cat.category).data)
            i += 1
        db.session.commit()
        flash(f"{monthstr}'s budget updated successfully!")
        return redirect(url_for('edit_budget', year=year, month=month))

    return render_template('budget_edit.html', title='Edit budget for ' + monthstr + ', ' + year, month=monthstr, \
            year=year, groups=groups, forms=forms, cats = cats, budget=budget)

@app.route('/budget/<year>/<month>', methods=['GET', 'POST'])
def review_budget(year, month):
    selectedmonth = datetime(int(year), int(month), 1).date()
    monthstr = datetime.strptime(month, '%m').strftime('%B')
    groups = CategoryGroup.query.all()
    cats = Category.query.order_by('id').all()
    budgetdata = MonthlyBudget.query.filter_by(date=selectedmonth).all()

    budget = {}
    for b in budgetdata:
        budget[b.category.category] = b.amount
    
    return render_template('budget_readonly.html', title='Budget for ' + monthstr + ', ' + year, month=monthstr, year=year, groups=groups, cats=cats, budget=budget)


# Edit after this

    # datenow = datetime.now().date()
    # thismonth = datetime(datenow.year, datenow.month, 1)
    # selectedmonth = datetime(int(year), int(month), 1)
    
    # # if month 2 less than current render a read only template
    # # if a budget exists for that month for all others then enter those into the boxes to be edited these should be updated don't create new budget
    # # Get average spent as recommendation for future budgets.
    # monthstr = datetime.strptime(month, '%m').strftime('%B')
    # groups = CategoryGroup.query.all()
    # cats = Category.query.order_by('id').all()
    # thisBudget = MonthlyBudget.query.filter_by(date=selectedmonth).all()
    # budget_exists = thisBudget.count() > 0
    # budgetdata = thisBudget.all()

    # budget = {}
    # for b in budgetdata:
    #     budget[b.category.category] = b.amount

    # twomonthsago = thismonth - relativedelta(months=2)
    # sixmonthsago = thismonth - relativedelta(months=6)
    # readOnly = thismonth < twomonthsago

    # forms = BudgetForm()

    # if forms.validate_on_submit():
    #     budget = []
    #     for cat in cats:
    #         budget.append(MonthlyBudget(amount=float(getattr(forms, cat.category).data), date=datetime(int(year),int(month),1).date(), category=cat))
    #     db.session.add_all(budget)
    #     db.session.commit()
    #     return redirect(url_for('budgets'))
    # elif request.method == 'GET':
    #     if readOnly:
            
    #     return render_template('budget.html', title='Budget for ' + monthstr + ', ' + year, month=monthstr, \
    #         year=year, groups=groups, forms=forms, cats = cats, budget=budget, budget_exists=budget_exists)

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
# https://blog.miguelgrinberg.com/post/using-celery-with-flask
# https://ondras.zarovi.cz/sql/demo/
# https://docs.sqlalchemy.org/en/14/orm/query.html?highlight=filter_by#sqlalchemy.orm.Query.filter_by
# https://wtforms.readthedocs.io/en/3.0.x/crash_course/
# https://trello.com/b/CbNxqs1J/budget-app
# https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#first-steps
# https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#broker-redis
# https://redis.io/docs/manual/admin/
# https://www.bbc.co.uk/sounds/play/m0018qxx    