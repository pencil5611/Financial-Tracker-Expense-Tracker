# Financial-Tracker-Expense-Tracker


## Features -
- CLI Expense Tracking 
- Allows you to add/view expenses that you've logged
- Stores data in csv files and reads from them to send weekly/monthly reports through email with pie charts
- stores email so you don't have to continuously input it
- ~250 keywords for autocategorization of expenses
- Groq AI to give in depth analysis, recommendations, and overall advice regarding user specific needs

## Actions -
- Add expenses → Add a transaction manually
- View expenses → Print all saved transactions
- Summarize Week → Weekly summary + pie chart + email
- Summarize Month → Monthly summary + pie chart + progress bar + email
- Budget Manual → Manually enter a budget
- Budget Calc → Calculate budget as % of income
- Set Goal → Allows user to set a monthly spending/saving goal, includes a progress bar in monthly report
- Use AI → Allows user to have a one on one conversation with the AI, where it has ready access to the users most recent monthly/weekly reports
- Set Email → Set destination email


## Requirements - 
- pip install python-dotenv, schedule, matplotlib, groq


## How to Use - 
- Install newest version of Python
- Install the previously mentioned requirements with pip
- go to groq.com and sign up for an API Key
- Create a .env file and store your email and app password as:
  EMAIL_ADDRESS=youremail@gmail.com
  PASSWORD=your_email_password_or_app_password
  api_key=entergroqapikeyhere
- run the program (main.py)
- choose an action by typing: add, view, summarize week, summarize month, budget manual, budget calc, set email, set goal, use ai, or exit. (NOTE: exit simply stops asking for an action and begins repeated monthly/weekly report scheduling, it will not shut off the program)


## OTHER NOTES -
- expenses are saved as expenses.csv
- budget is saved as budget.csv
- recipient email is saved as emailaddress.csv
- pie charts for reports are saved as images (piechart.png for month and piechartweek.png for week)
- weekly/monthly summaries are saved to respective .txt files for the AI's access
- If you found this useful, feel free to star it so other people can stumble upon it more easily :)
