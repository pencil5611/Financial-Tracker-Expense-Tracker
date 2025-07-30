import csv
import os
import sys
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
import schedule
import time
import matplotlib.pyplot as plt
from keywords import keyword_map

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("PASSWORD")


USER_BUDGET_MONTH_FILE = 'budget.csv'
if not os.path.exists(USER_BUDGET_MONTH_FILE):
    with open(USER_BUDGET_MONTH_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Monthly Budget"])


STORE_EMAIL_FILE = 'emailaddress.csv'
if not os.path.exists(STORE_EMAIL_FILE):
    with open(STORE_EMAIL_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Email Address"])


EXPENSES_FILE = 'expenses.csv'
if not os.path.exists(EXPENSES_FILE):
    with open(EXPENSES_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Category", "Amount"])


def calculate_budget():
    while True:
        print('Input your take home monthly income')
        try:
            income = float(input('>'))
            print('What % of that would you like to allocate towards spending? (Enter a whole number. eg, 50 for 50%)')
            percent_spend = float(input('>')) / 100
            budget_calc = income * percent_spend
            with open(USER_BUDGET_MONTH_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([budget_calc])
                print(f"Your budget is ${budget_calc}")
                break
        except ValueError:
            print('Please enter a number.')

def get_recipient():
    global RECIPIENT
    print('Please enter email address')
    RECIPIENT = input('>')
    with open(STORE_EMAIL_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([RECIPIENT])

def recipient_for_send():
    with open(STORE_EMAIL_FILE, 'r', newline='') as file:
        reader = list(csv.reader(file))
        if len(reader) > 1:
            return reader[-1][0]
        else:
            return None

RECIPIENT = recipient_for_send()

def add_expense():
    global date_obj
    while True:
        try:
            print('Please enter the date of this expense. eg: July 27, 2025')
            date = input('>')
            date_obj = datetime.strptime(date, '%B %d, %Y')
            break
        except ValueError:
            print('Please enter a valid date')
    print('Please enter the description of the expense.')
    description = input('>')
    category = auto_categorize(description)
    if category != 'uncategorized':
        print(f"Auto-categorizing description: '{description}' as '{category}'")
    while True:
        category = category.lower()
        if category == 'uncategorized':
            print('Failed to auto-categorize, please enter category manually.')
            print('Please enter the category of the expense. CUSTOM, Housing, Food, Transportation, Insurance, Health, Debts, Clothes, Personal Care, Investments, Subscriptions, Entertainment, Utilities, Misc')
            category = input('>').lower()
        possible_categories = ['housing', 'utilities', 'food', 'groceries', 'transportation', 'insurance', 'health', 'entertainment', 'debts', 'clothes', 'subscriptions', 'personal care', 'investments', 'misc', 'custom']
        if category not in possible_categories:
            print('Please enter a valid category')
            category = input('>')
        else:
            break
    if category == 'custom':
        print('Please enter the category of the expense.')
        category = input('>').lower()
    print('Please enter the amount of the expense.')
    amount = input('>')
    with open(EXPENSES_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date_obj.strftime('%Y-%m-%d'), description, category, amount])



def auto_categorize(description):
    description = description.lower()
    for keyword, category in keyword_map.items():
        if keyword in description:
            return category
    return "uncategorized"



def view_expenses():
    with open(EXPENSES_FILE, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)


today = datetime.today()
seven_days_ago = today - timedelta(days=7)
def weekly_expenses():
    global total
    category_totals = defaultdict(float)
    recent_rows = []
    with open(EXPENSES_FILE, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)
        total = 0
        for row in reader:
            try:
                row_date = datetime.strptime(row[0], '%Y-%m-%d')
                if seven_days_ago <= row_date <= today:
                    amount_str = row[3].replace(',', '')
                    amount = float(amount_str)
                    category = row[2].lower()
                    total += amount
                    category_totals[category] += amount
                    recent_rows.append(row)
            except (ValueError, IndexError):
                continue

    summary = f"Weekly Expenses Summary ({seven_days_ago.date()} to {today.date()}):\n"
    for row in recent_rows:
        summary += f"- {row[0]} | {row[1]} | {row[2]} | ${row[3]}\n"

    summary += "\n\nExpenses by Category:\n"
    for category, amount in category_totals.items():
        summary += f"- {category.title()}: ${round(amount, 2)}\n"
    summary += f"\nTotal: ${round(total, 2)}"
    return summary



def send_email(body, attachment_path=None):
    msg = EmailMessage()
    msg['subject'] = 'Expenses Report'
    msg['from'] = EMAIL_ADDRESS
    msg['to'] = RECIPIENT
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, 'rb') as file:
            file_data = file.read()
            file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype='image', subtype='png', filename=file_name)


    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, PASSWORD)
        smtp.send_message(msg)


def budget():
    global user_budget
    global perc_budget_used
    print('Please enter monthly budget')
    while True:
        try:
            user_budget = float(input('>'))
        except ValueError:
            print('Please enter a valid number.')
        with open(USER_BUDGET_MONTH_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_budget])
            print(f"Your budget is ${user_budget}")
            break



def get_latest_budget():
    try:
        with open(USER_BUDGET_MONTH_FILE, 'r', newline='') as file:
            reader = list(csv.reader(file))
            if len(reader) > 1:
                return float(reader[-1][0])
    except:
        pass
    return None


def monthly_expenses():
    global month_total
    budget_real = get_latest_budget()
    thirty_days_ago = today - timedelta(days=30)
    month_total = 0
    category_totals = defaultdict(float)
    recent_rows = []
    if budget_real is None:
        print('Please enter a valid monthly budget.')
    else:
        with open(EXPENSES_FILE, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                try:
                    row_date = datetime.strptime(row[0], '%Y-%m-%d')
                    if thirty_days_ago <= row_date <= today:
                        amount_str = row[3].replace(',', '')
                        amount = float(amount_str)
                        category = row[2].lower()
                        month_total += amount
                        category_totals[category] += amount
                        recent_rows.append(row)
                except (ValueError, IndexError):
                    continue
    summary = f"Monthly Expense Summary ({thirty_days_ago.date()} to {today}):\n"
    for row in recent_rows:
        summary += f"- {row[0]} | {row[1]} | {row[2]} | ${row[3]}\n"
    summary += "\n\nExpenses by Category:\n"
    for category, amount in category_totals.items():
        summary += f"- {category.title()}: ${round(amount, 2)}\n"

    summary += f"Total: ${round(month_total, 2)}"
    return summary


def job_monthly():
    summary = monthly_expenses()
    budget_real = get_latest_budget()
    if budget_real is not None and month_total > 0:
        perc_budget_used_month = round(float((month_total / budget_real)) * 100, 2)
        summary += f"\nYour monthly budget is ${budget_real}."
        summary += f"\nYou used {perc_budget_used_month}% of the monthly budget this past month"
    elif budget_real is None:
        summary += f"\nYou have not set any budget"
    if float(month_total) > float(budget_real):
        summary += f"\nYou spent ${float(month_total) - float(budget_real)} more than your budget."
    elif float(month_total) < float(budget_real):
        summary += f"\nYou saved ${float(budget_real) - float(month_total)} this month by spending less than your budget."
    print(summary)
    show_pie_chart_monthly()
    send_email(summary, 'piechart.png')


def job():
    summary = weekly_expenses()
    budget_amount = get_latest_budget()
    if budget_amount is not None and total > 0:
        perc_budget_used = round((total / budget_amount) * 100, 2)
        summary += f"\nYour monthly budget is ${budget_amount}"
        summary += f"\nYou have used {perc_budget_used}% of your monthly budget this week."
    elif budget_amount is None:
        summary += f"\nYou have not set any budget"
    else:
        summary += f"\nYou have not spent any money"
    print(summary)
    show_pie_chart_weekly()
    send_email(summary, 'piechartweek.png')


def show_pie_chart_monthly():
    thirty_days_ago = today - timedelta(days=30)
    category_totals = defaultdict(float)
    with open('expenses.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if len(row) < 4:
                continue
            _, _, category, amount = row
            try:
                row_date = datetime.strptime(row[0], '%Y-%m-%d')
                if thirty_days_ago <= row_date <= today:
                    amount_str = row[3].replace(',', '')
                    amount = float(amount_str)
                    category = row[2].strip().lower()
                    category_totals[category.strip()] += float(amount)
                if not category_totals:
                    print("No data found for the last 30 days.")
                    return
            except ValueError:
                continue
    labels = list(category_totals.keys())
    values = list(category_totals.values())
    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f'Expenses by Category\n({thirty_days_ago.strftime("%Y-%m-%d")} to {today.strftime("%Y-%m-%d")})')
    plt.axis('equal')
    plt.savefig('piechart.png')
    plt.close()


def show_pie_chart_weekly():
    seven_days_ago = today - timedelta(days=7)
    category_totals = defaultdict(float)
    with open('expenses.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if len(row) < 4:
                continue
            _, _, category, amount = row
            try:
                row_date = datetime.strptime(row[0], '%Y-%m-%d')
                if seven_days_ago <= row_date <= today:
                    amount_str = row[3].replace(',', '')
                    amount = float(amount_str)
                    category = row[2].strip().lower()
                    category_totals[category.strip()] += float(amount)
                if not category_totals:
                    print("No data found for the last 7 days.")
                    return
            except ValueError:
                continue
    labels = list(category_totals.keys())
    values = list(category_totals.values())
    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f'Expenses by Category\n({seven_days_ago.strftime("%Y-%m-%d")} to {today.strftime("%Y-%m-%d")})')
    plt.axis('equal')
    plt.savefig('piechartweek.png')
    plt.close()


print('Welcome to Financial Tracker!')
try:
    while True:
        options = ['view', 'add', 'exit', 'summarize week', 'summarize month', 'budget manual', 'budget calc', 'set email']
        print('What would you like to do? Options: Add expenses, View expenses, Summarize Week, Summarize Month, Budget Manual, Budget Calc, Set Email, or Exit.')
        choice = input('>').lower()
        if choice not in options:
            print('Please enter a valid option.')
        elif choice == 'view':
            view_expenses()
        elif choice == 'budget manual':
            budget()
        elif choice == 'budget calc':
            calculate_budget()
        elif choice == 'set email':
            get_recipient()
        elif choice == 'add':
            add_expense()
        elif choice == 'summarize week':
            job()
        elif choice == 'summarize month':
            job_monthly()
        elif choice == 'exit':
            break
except KeyboardInterrupt:
    print('Thank you for using Financial Tracker!')
    sys.exit(0)




def is_first_of_month():
    return datetime.now().day == 1

def monthly_task_wrapper():
    if is_first_of_month():
        job_monthly()

schedule.every().saturday.at("12:00").do(job)
schedule.every().day.at("12:00").do(monthly_task_wrapper)
try:
    while True:
        schedule.run_pending()
        time.sleep(60)
except KeyboardInterrupt:
    sys.exit(0)
