import logging
import pickle
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler

TOKEN_BOT = palint
user_data = {}
list_category = ['food', 'water', 'gas']

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

week_ago = datetime.now() - timedelta(weeks=1)
month_ago = datetime.now() - timedelta(weeks=4)
current_date = datetime.now()

class Cost:
    """
        transactions
    """
    def __init__(self, type_cat: str, money: float, category: str, date_cost: datetime = None):
        self.type_cat = type_cat
        self.money = money
        self.category = category
        self.date_cost = date_cost

    def __str__(self):
        if self.type_cat == "income":
            return f'{self.type_cat}: {self.money} , {self.category}, {self.date_cost.strftime("%Y-%m-%d %H:%M")}'
        else:
            return f'{self.type_cat}    : {self.money} , {self.category}, {self.date_cost.strftime("%Y-%m-%d %H:%M")}'

# save data ins file
def save_data():
    with open('user_data.pkl', 'wb') as file:
        pickle.dump(user_data, file)

# load data in file
def load_data():
    global user_data
    try:
        with open('user_data.pkl', 'rb') as file:
            user_data = pickle.load(file)
    except FileNotFoundError:
        user_data = {}

async def start(update: Update, contex: CallbackContext) -> None:
    logging.info('Command "start" was triggerd')
    await update.message.reply_text(
        "Welcome to MoneyTracker Bot!\n"
        "Commands: \n"
        "/cost [money], [category] ,[date not required]\n" #1. Мати можливість додавати витрати вказуючи категорію
        "/in [money],[category default ocher for today],[date not required] \n" #4. Додавати доходи з вказанням категорії доходів
        "date format: Y-M-D or date+time y-m-d h:m \n" 
        "/list_cat allow cat for cost \n"                           #3. Повертати список доступних категорій
        "/list all costs, options[week,month, all (income include)] \n"#5. Можливість переглядати всі витрати, витрати за місяць та за тиждень.
        "/rem [index] remove transaction\n"                         #6. Видаляти витрати або доходи
        "/clear  clear all transaction: \n"
        "/st statistics today cost [week, month, year] \n"   #5. Можливість переглядати всі витрати, витрати за місяць та за тиждень.
        "/st [in] today income, [week, month, year] \n" #5. Можливість переглядати всі витрати, витрати за місяць та за тиждень.
        "[YYYY] - set year, [YYYY-M] set month\n"
    )

async def add_cost(update: Update, context: CallbackContext) -> None:
    """
    Format of cost  command
    /add cost [ , , ]
    """
    user_id = update.message.from_user.id
    cost_parts = " ".join(context.args).split(",")
    transaction_date = current_date
    if len(cost_parts) not in [2, 3]:
        await update.message.reply_text("Incorrect: example /cost 200,food or /cost 200.20,food,2023-01-02")
        return
    cost_money = cost_parts[0].strip()

    if re.match(r'^[+]?[0-9]+(\.[0-9]{1,2})?$', cost_money):    # check int or float format money
        cost_category = cost_parts[1].strip()
        if cost_category in list_category:
            if len(cost_parts) == 3:
                try:
                    transaction_date = datetime.strptime(cost_parts[2].strip(), '%Y-%m-%d')
                except ValueError:
                    try:
                        transaction_date = datetime.strptime(cost_parts[2].strip(), '%Y-%m-%d %H:%M')
                    except ValueError:
                        logging.error("Invalid date format")
                        await update.message.reply_text("Your data enter invalid, please enter correct"
                                                        "correct example 2023-12-01 or 2023-12-01 14:20 ")
                        return
        else:
            await update.message.reply_text("Your category enter is invalid, (/list_cat for allowed cat)")
            return
        if not user_data.get(user_id):
            user_data[user_id] = []
    else:
        await update.message.reply_text("Incorrect money format, example: \n"
                                        " /cost 200,food or /cost 200.20,food,2023-01-02")
        return
    cost = Cost('costs', float(cost_money), cost_category, transaction_date)
    user_data[user_id].append(cost)
    await update.message.reply_text(f"{cost} was successfully added!")

async def add_income(update: Update, context: CallbackContext) -> None:
    """
    Format of income  command
    /income [money, type , date ]
    """
    user_id = update.message.from_user.id
    income_parts = " ".join(context.args).split(",")
    date_in = datetime.now()

    if len(income_parts) in [1, 2, 3]:
        income_money = income_parts[0].strip()
        if re.match(r'^[+]?[0-9]+(\.[0-9]{1,2})?$', income_money):

            if len(income_parts) == 1:
                income_category = 'other'
            else:
                income_category = income_parts[1].strip()
            if len(income_parts) == 3:
                try:
                    date_in = datetime.strptime(income_parts[2].strip(), '%Y-%m-%d')
                except ValueError:
                    try:
                        date_in = datetime.strptime(income_parts[2].strip(), '%Y-%m-%d %H:%M')
                    except ValueError:
                        logging.error("Invalid date format")
                        await update.message.reply_text("Your data enter invalid, please enter correct")
                        return
        else:
            await update.message.reply_text("Incorrect money format, example \n "
                                                "/in 200 or /in 200,salary or /in 200, salary, 2023-01-02")
            return
    else:
        await update.message.reply_text("Incorrect input format, example:\n"
                                        "/in 200 or /in 200,salary or /in 200,salary, 2023-01-02:")
        return

    if not user_data.get(user_id):
        user_data[user_id] = []

    income = Cost('income', float(income_money), income_category, date_in)
    user_data[user_id].append(income)
    await update.message.reply_text(f"{income} was successfully added!")

async def list_cost(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    command_parts = context.args

    if not user_data.get(user_id):
        await update.message.reply_text("You don't have any ...")
        return

    result = []
    if len(command_parts) == 0:  #/list all costs
        for i, t in enumerate(user_data[user_id]):
            if hasattr(t, 'type_cat') and t.type_cat == 'costs':
                result.append(f"{i + 1}. {t}")
    elif len(command_parts) == 1:   # list month ago cost
        param = command_parts[0]
        if param == "month":
            for i, t in enumerate(user_data[user_id]):
                if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost >= month_ago:
                    result.append(f"{i + 1}. {t}")
        elif param == "week":
            for i, t in enumerate(user_data[user_id]):
                if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost >= week_ago:
                    result.append(f"{i + 1}. {t}")
        elif param == "all":    # list all transaction
            for i, t in enumerate(user_data[user_id]):
                if hasattr(t, 'type_cat'):
                    result.append(f"{i + 1}. {t}")
        else:
            # Обробити невідомий параметр
            await update.message.reply_text("Unknown parameter, allow: week, month, year, all.")
            return

    else:
        # Обробити невірну кількість параметрів
        await update.message.reply_text("Allow one param: week, month, year, all.")
        return
    if result:
        await update.message.reply_text('\n'.join(result))
    else:
        await update.message.reply_text("No transaction")

async def stats(update: Update, context: CallbackContext) -> None:
    """
        Format of stats  command
        /st [],[],[]
    """
    user_id = update.message.from_user.id
    command_parts = context.args

    async def calc(res):   #calc and return sum in cat
        cat = {}
        for row in res:
            parts = row.split(",")  # Розділити рядок за комами
            category = parts[1].strip()  # Отримати категорію (елемент після першої коми)
            amount = float(parts[0].split(",")[0])  # Отримати суму (елемент перед першою крапкою)

            if category in cat:
                cat[category] += amount
            else:
                cat[category] = amount
        if not cat:
            await update.message.reply_text("There is nothing")
        else:
            for category, amount in cat.items():
                await update.message.reply_text(f"{category}: {amount}")

    if not user_data.get(user_id):
        await update.message.reply_text("You don't have any ...")
        return

    result = []
    if len(command_parts) > 2:
        await update.message.reply_text("Incorrect option")
    else:
        if len(command_parts) == 0:  # /st(today costs)
            for i, t in enumerate(user_data[user_id]):
                if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost.date() == current_date.date():
                    result.append(f"{t.money}, {t.category}")
            await calc(result)

        elif len(command_parts) == 1:
            param = command_parts[0]
            if param == "week":   # /st week = last week costs sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost >= week_ago:
                        result.append(f"{t.money}, {t.category}")

            elif param == "month":  # /st month = current month costs sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost.month == current_date.month:
                        result.append(f"{t.money}, {t.category}")

            elif param == "year":  # /st year = current year cost sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost.year == current_date.year:
                        result.append(f"{t.money}, {t.category}")

            elif param == "in":    # /st in = today income sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'income' and t.date_cost.date() == current_date.date():
                        result.append(f"{t.money}, {t.category}")

            elif re.match(r"^\d{4}$", param): # /st 2023  = sum out write year
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'costs' and t.date_cost.year == int(param):
                        result.append(f"{t.money}, {t.category}")

            elif re.match(r"^\d{4}-\d{1,2}$", param):  # /st xxxx-xx  = sum in write year-month
                year, month = param.split("-")
                year = int(year)
                month = int(month)
                for i, t in enumerate(user_data[user_id]):

                    if hasattr(t, 'type_cat') and \
                            t.type_cat == 'costs' and t.date_cost.year == year and t.date_cost.month == month:
                        result.append(f"{t.money}, {t.category}")
            else:
                await update.message.reply_text("Unknown param.")
                return
            await calc(result)

        elif len(command_parts) == 2 and command_parts[0] == 'in':
            param2 = command_parts[1]
            if param2 == "week":  # /st in week = last week income sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'income' and t.date_cost >= week_ago:
                        result.append(f"{t.money}, {t.category}")

            elif param2 == "month":  # /st in month = current month income sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'income' and t.date_cost.month == current_date.month:
                        result.append(f"{t.money}, {t.category}")

            elif param2 == 'year': # /st in year = current year income sum in cat
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'income' and t.date_cost.year == current_date.year:
                        result.append(f"{t.money}, {t.category}")

            elif re.match(r"^\d{4}$", param2): # /st in 2023  = sum in write year
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and t.type_cat == 'income' and t.date_cost.year == int(param2):
                        result.append(f"{t.money}, {t.category}")

            elif re.match(r"^\d{4}-\d{1,2}$", param2):  # /st in xxxx-xx  = sum in write year-month
                year, month = param2.split("-")
                year = int(year)
                month = int(month)
                for i, t in enumerate(user_data[user_id]):
                    if hasattr(t, 'type_cat') and \
                            t.type_cat == 'income' and t.date_cost.year == year and t.date_cost.month == month:
                        result.append(f"{t.money}, {t.category}")
            else:
                await update.message.reply_text("Unknown param.")
                return
            await calc(result)

async def list_cat(update: Update, context: CallbackContext) -> None:
    """
        Format of list_cat
        /list_cat
    """
    formatted_list = '\n'.join([f'{category}' for i, category in enumerate(list_category)])
    await update.message.reply_text(f"Category list:\n {formatted_list}")

async def remove(update: Update, context: CallbackContext) -> None:
    """
        Format of remove  command
        /rem [index]
    """
    user_id = update.message.from_user.id
    if not user_data.get(user_id):
        await update.message.reply_text("You don't have any transaction to remove")
        return
    try:
        removed_idx = int(context.args[0]) - 1
        transaction = user_data[user_id].pop(removed_idx)
        await update.message.reply_text(f"{transaction} successfully removed")
    except (ValueError, IndexError):
        await update.message.reply_text("You entered an invalid index.")

async def clear(update: Update, context: CallbackContext) -> None:
    """
        /clear
    """
    user_id = update.message.from_user.id
    user_data[user_id] = []
    await update.message.reply_text("Cleared All successfully")

def run():

    # load data in run
    load_data()

    app = ApplicationBuilder().token(TOKEN_BOT).build()
    logging.info("Application built successfully!")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("list_cat", list_cat))
    app.add_handler(CommandHandler("cost", add_cost))
    app.add_handler(CommandHandler("list", list_cost))
    app.add_handler(CommandHandler("rem", remove))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("in", add_income))
    app.add_handler(CommandHandler("st", stats))


    try:
        app.run_polling()
    finally:
        # save data in close
        save_data()


if __name__ == "__main__":
    run()
