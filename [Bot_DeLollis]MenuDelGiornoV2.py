import logging

from bs4 import BeautifulSoup
import requests
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

keyboard = [
        [
            InlineKeyboardButton("Mon", callback_data=0),
            InlineKeyboardButton("Tue", callback_data=1),
            InlineKeyboardButton("Wen", callback_data=2),
            InlineKeyboardButton("Thu", callback_data=3),
            InlineKeyboardButton("Fri", callback_data=4),
            InlineKeyboardButton("Sat", callback_data=5),
        ],
    ]

reply_markup = InlineKeyboardMarkup(keyboard)

start_m = """I can send you the menu of the DeLollis canteen of today or the entire week.

You can control me by sending these commands:

❓   /help - list of commands

*Get your Menu*
  🗓  /week - sends you the whole week worth of menu (lunch + dinner)
  🍗🥂/menu - sends you today's menu (lunch + dinner) 
  🍗  /lunch - sends you the afternoon menu of the current day (WIP)
  🥂  /dinner - sends you the evening menu of the current day (WIP)"""

err_m = ""

logger = logging.getLogger(__name__)

daysList = ["Lunedì non trovato", "Martedì non trovato", "Mercoledì non trovato", "Giovedì non trovato",
                "Venerdì non trovato", "Sabato non trovato"]
pranzoL = ["Pranzo di oggi non trovato"] * 6
cenaL = ["Cena di oggi non trovata"] * 6
cenaL[5] = "Il sabato la cena non c'è"
giornata = []
weekDay = datetime.date.today().isocalendar()[2]
msgFestivo = ""

def get_that_week():
    url = 'https://www.cimasristorazione.com/menu-mense/universita-roma-1/'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    try:
        # Trova il menù della settimana
        week = soup.find_all('div', {'class': 'col-12 col-md-6 col-lg-4 day-menu'})
        natale = soup.find('div', {'class': 'col-12 jumbotron'})
        if not week:
            natale = soup.find('div', {'class': 'col-12 jumbotron'})
            msgFestivo = ""
            for child in natale.children:
                msgFestivo += child.string + "\n"
            return
        # Per ogni giorno prendi il menù!
        for day in range(len(week)):
            pranzo = str(week[day].find('div', {'id': "pranzo-" + str(day + 1)})).replace("</li> <li>", "\n# ").replace(
                "</h5> <ul> <li>", " --\n# ").replace("</li> </ul> <h5>", "\n\n-- ").replace(
                """<div class="tab-pane fade show active" id="pranzo-""" + str(day + 1) + """" role="tabpanel"> <h5>""",
                "\nPRANZO\n-- ").replace("</li> </ul> </div>", "\n").replace("</h5>     <ul> <li>", " --\n# ")
            if pranzo != "None":
                pranzoL[day] = pranzo
            cena = str(week[day].find('div', {'id': "cena-" + str(day + 1)})).replace("</li> <li>", "\n# ").replace(
                "</h5> <ul> <li>", " --\n# ").replace("</li> </ul> <h5>", "\n\n-- ").replace(
                """<div class="tab-pane fade" id="cena-""" + str(day + 1) + """" role="tabpanel"> <h5>""",
                "\nCENA\n-- ").replace("</li> </ul> </div>", "\n").replace("</h5>     <ul> <li>", " --\n# ").replace(
                "</h5> </div>", "🎄")

            if cena != "None":
                cenaL[day] = cena


            if day + 1 == weekDay:
                giornata.append("*[ " + week[day].find('div', {'class': "col-header"}).text.strip().replace(" ", " - ", 1) + " ]*\n")
            messaggio = "*[ " + week[day].find('div', {'class': "col-header"}).text.strip().replace(" ", " - ", 1) + " ]*\n" + pranzoL[day] + "\n" + cenaL[day]
            daysList[day % 6] = messaggio

    except:
        err_m = "\nAlcuni Menù non sono stati trovati!"
    return giornata

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(start_m, parse_mode=ParseMode.MARKDOWN)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery

    query.edit_message_text(text=daysList[int(query.data)], reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(start_m, parse_mode=ParseMode.MARKDOWN)


def week_command(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    #update.message.reply_text(err_m)
    if not daysList[0] == "Lunedì non trovato":
        update.message.reply_text(daysList[0], reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        get_that_week()
        update.message.reply_text(daysList[0], reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


def menu_command(update: Update, context: CallbackContext) -> None:
    if msgFestivo != "":
        update.message.reply_text(msgFestivo)
    elif not daysList[0] == "Lunedì non trovato":
        update.message.reply_text(daysList[weekDay - 1], parse_mode=ParseMode.MARKDOWN)
    else:
        get_that_week()
        update.message.reply_text(daysList[weekDay - 1], parse_mode=ParseMode.MARKDOWN)


def lunch_command(update: Update, context: CallbackContext) -> None:
    if not daysList[0] == "Lunedì non trovato":
        update.message.reply_text(giornata[0] + pranzoL[weekDay - 1], parse_mode=ParseMode.MARKDOWN)
    else:
        get_that_week()
        update.message.reply_text(giornata[0] + pranzoL[weekDay - 1], parse_mode=ParseMode.MARKDOWN)


def dinner_command(update: Update, context: CallbackContext) -> None:
    if not daysList[0] == "Lunedì non trovato":
        update.message.reply_text(giornata[0] + cenaL[weekDay - 1], parse_mode=ParseMode.MARKDOWN)
    else:
        get_that_week()
        update.message.reply_text(giornata[0] + cenaL[weekDay - 1], parse_mode=ParseMode.MARKDOWN)


def main() -> None:
    """Run the bot."""
    get_that_week()
    # Create the Updater and pass it your bot's token.
    updater = Updater("5001378659:AAGu4kGDG-sgekQknyzIVJwCloVsUMlXdms")
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(CommandHandler('week', week_command))
    updater.dispatcher.add_handler(CommandHandler('menu', menu_command))
    updater.dispatcher.add_handler(CommandHandler('lunch', lunch_command))
    updater.dispatcher.add_handler(CommandHandler('dinner', dinner_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
