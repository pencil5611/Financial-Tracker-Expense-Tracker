# Financial-Tracker-Expense-Tracker


## Features -
- Allows you to add/view expenses that you've logged
- Stores data in csv files and reads from them to send weekly/monthly reports through email with pie charts
- stores email so you don't have to continuously input it
- ~250 keywords for autocategorization of expenses

## Actions -
- Add expenses → Add a transaction manually
- View expenses → Print all saved transactions
- Summarize Week → Weekly summary + pie chart + email
- Summarize Month → Monthly summary + pie chart + email=
- Budget Manual → Manually enter a budget
- Budget Calc → Calculate budget as % of income
- Set Email → Set destination email


## Requirements - 
- pip install python-dotenv, schedule, matplotlib


## How to Use - 
- Install newest version of Python
- Install the previously mentioned requirements with pip
- Create a .env file and store your email and app password as:
  EMAIL_ADDRESS=youremail@gmail.com
  PASSWORD=your_email_password_or_app_password
- run the program (main.py)
- choose an action by typing: add, view, summarize week, summarize month, budget manual, budget calc, set email, or exit. (NOTE: exit simply stops asking for an action and begins repeated monthly/weekly report scheduling, it will not shut off the program)


## OTHER NOTES -
- expenses are saved as expenses.csv
- budget is saved as budget.csv
- recipient email is saved as emailaddress.csv
- pie charts for reports are saved as images (piechart.png for month and piechartweek.png for week)
