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
from groq import Groq
import json
load_dotenv()

api_key = os.getenv('API_KEY')
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



GOAL_FILE = 'goal.json'

def set_goal():
    global goal_amount
    allowed_goals = ['spending', 'saving']

    while True:
        print('What type of goal would you like to set? Spending or Saving?')
        goal_type = input('>').strip().lower()

        if goal_type not in allowed_goals:
            print('Please enter a valid goal type.')
            continue

        try:
            print('What is the goal amount?')
            goal_amount = float(input('>'))
            break
        except ValueError:
            print('Please enter a valid number.')

    with open(GOAL_FILE, 'w') as f:
        json.dump({'type': goal_type, 'amount': goal_amount}, f)

    print(f'{goal_type.title()} goal of ${goal_amount:.2f} has been set.')



def load_goal():
    if not os.path.exists(GOAL_FILE):
        return None
    with open(GOAL_FILE, 'r') as f:
        return json.load(f)

def show_progress_bar(spent_total):
    global goal_type
    goal = load_goal()
    if not goal:
        print('No goal.')
        return
    goal_amount = goal['amount']
    goal_type = goal['type']

    if goal_type == 'spending':
        percent = min(spent_total / goal_amount, 1.0)
        remaining = max(goal_amount - spent_total, 0)
        label = f"Spent ${spent_total:.2f} / ${goal_amount:.2f} (Remaining: ${remaining:.2f})"
    elif goal_type == 'saving':
        percent = min(spent_total / goal_amount, 1.0)
        label = f"Saved ${spent_total:.2f} / ${goal_amount:.2f}"
    else:
        print("Unknown goal type.")
        return

    bar_len = 30
    filled = int(bar_len * percent)
    bar = '█' * filled + '-' * (bar_len - filled)
    print(f"[{bar}] {percent * 100:.1f}%\n{label}")
    return f"[{bar}] {percent * 100:.1f}%\n{label}"



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
            print('Please enter the category of the expense. CUSTOM, Housing, Food, Transportation, Insurance, Health, Debts, Clothes, Personal Care, Investments, Subscriptions, Entertainment, Utilities, Misc, Travel')
            category = input('>').lower()
        possible_categories = ['housing', 'utilities', 'food', 'groceries', 'transportation', 'insurance', 'health', 'entertainment', 'debts', 'clothes', 'subscriptions', 'personal care', 'investments', 'misc', 'custom', 'travel']
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


groq_client = Groq(api_key=api_key)
def ai_auto_categorize(description):
    possible_cats = 'Housing, Food, Transportation, Insurance, Health, Debts, Clothes, Personal Care, Investments, Subscriptions, Entertainment, Utilities, Travel, Misc'
    prompt = f"Categorize the following expense: '{description}' into one of the following categories: {possible_cats}. Write only the category name, NOTHING ELSE."
    # noinspection PyTypeChecker
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip().lower()


def auto_categorize(description):
    description = description.lower()
    for keyword, category in keyword_map.items():
        if keyword in description:
            return category
    try:
        return ai_auto_categorize(description)
    except Exception:
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
    saved = 0
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
        saved = float(budget_real) - float(month_total)
        summary += f"\nYou saved ${float(budget_real) - float(month_total)} this month by spending less than your budget."
    else:
        summary += "\nYou hit your budget exactly."
    recommendations_month = ai_recs_monthly(summary)
    summary += f"\n\nAI Recommendations:\n{recommendations_month}"
    print(summary)
    try:
        show_pie_chart_monthly()
        assert os.path.exists('piechart.png'), "Pie chart image not found."
    except (ValueError, IndexError, ZeroDivisionError) as e:
        summary += f"\nCould not generate pie chart due to data issues: {e}"
    except (IOError, AssertionError) as e:
        summary += f"\nPie chart file error: {e}"
    try:
        goal = load_goal()
        goal_type = goal['type']
        if goal_type == 'saving':
            bar = show_progress_bar(saved)
        else:
            bar = show_progress_bar(month_total)
        summary += f'\n\n{bar}'
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        summary += "\nNo goal data found or file is corrupted."
    with open('monthly_summary.txt', 'w', newline='') as f:
        f.write(summary)
    try:
        send_email(summary, 'piechart.png')
    except FileNotFoundError:
        send_email(summary + "\n(Note: Pie chart image was not attached due to a generation error.)")


def ai_recs_monthly(summary):
    prompt = f"Based on the following monthly expenses summary, briefly analyze and then provide 3 short, actionable budgeting or financial tips: {summary}"
    try:
        # noinspection PyTypeChecker
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        if not hasattr(response, "choices") or not response.choices:
            return "AI returned an empty or invalid response."
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI Error] {e}")
        return "AI could not generate recommendations at this time."





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
    recommendations = ai_recs_weekly(summary)
    summary += f"\n\nAI Recommendations:\n{recommendations}"
    with open('weekly_summary.txt', 'w') as f:
        f.write(summary)
    print(summary)
    show_pie_chart_weekly()
    send_email(summary, 'piechartweek.png')

def ai_recs_weekly(summary):
    prompt = f"Based on the following weekly expenses summary, briefly analyze and then provide 3 short, actionable budgeting or financial tips: {summary}"
    try:
        # noinspection PyTypeChecker
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        if not hasattr(response, "choices") or not response.choices:
            return "AI returned an empty or invalid response."

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[AI Error] {e}")
        return "AI could not generate recommendations at this time."



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


def use_ai():
    print("💬 Welcome to your AI financial assistant.")
    print("Ask any question about your spending, budget, savings, or financial goals.")
    print("Type 'exit' to quit.\n")
    context = ''
    if os.path.exists('weekly_summary.txt'):
        with open('weekly_summary.txt') as file:
            context += f'Weekly Summary:\n{file.read()}\n\n'
    if os.path.exists('monthly_summary.txt'):
        with open('monthly_summary.txt') as file:
            context += f'Monthly Summary:\n{file.read()}\n\n'

    system_prompt = {
        "role": "system",
        "content": f'You are a financial expert helping a user manage their personal budget, categorize expenses, optimize spending, and reach savings goals. Answer clearly and concisely. Recent context:\n{context}'
    }

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting AI assistant.")
            break

        try:
            # noinspection PyTypeChecker
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    system_prompt,
                    {"role": "user", "content": user_input}
                ],
                temperature=0.5,
                max_tokens=800
            )
            ai_reply = response.choices[0].message.content.strip()
            print(f"AI: {ai_reply}\n")
        except Exception as e:
            print(f"Error: {e}")
            print("Something went wrong with the AI. Try again later.")

print('Welcome to Financial Tracker!')
try:
    while True:
        options = ['view', 'add', 'exit', 'summarize week', 'summarize month', 'budget manual', 'budget calc', 'set email', 'use ai', 'set goal']
        print('What would you like to do? Options: Add expenses, View expenses, Summarize Week, Summarize Month, Use AI, Budget Manual, Budget Calc, Set Email, Set Goal, or Exit.')
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
        elif choice == 'set goal':
            set_goal()
        elif choice == 'use ai':
            use_ai()
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
