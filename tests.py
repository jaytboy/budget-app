from datetime import datetime
from dateutil.relativedelta import relativedelta

datenow = datetime.now().date()
thismonth = datetime(datenow.year, datenow.month, 1).date()
twomonthsago = thismonth - relativedelta(months=2)
# Read about time and servers here: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xii-dates-and-times
# Seems like a good chance for pagenation or toggel months of a given year.
    
data = [datetime(2022, 3, 1).date(), datetime(2022, 4, 1).date(), datetime(2022, 5, 1).date(), \
datetime(2022, 6, 1).date(), datetime(2022, 7, 1).date(), datetime(2022, 8, 1).date()]
years = {}
dates = []
# FIX THIS!!!!
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

for year in years:
    print(year)