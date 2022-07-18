# python3

"""Steps for creating Telegram bot
1. Create prototype function first (that is, start function, main function with ConversationHandler and CommandHandler
2. For each additional functionality that you want to create, do the following:
A: Create the function
B: Create a state for the function (FIRSTSTEP = 0)
C: Add the state to the ConversationHandler, in dictionary states
D: For the previous function, return the next state (this is how you transition between states!)
    Eg: If you finished fn at FIRSTSTEP, let that function return SECONDSTEP

Common format for function in Telegram Bot:
1. Store information received from previous step (if not first step)
    This is because the reply that was sent that triggered the function, is the response to previous function
2. Manipulate information if needed
3. Set up for next function
4. Reply to user


This bot has a very simple functionality: It asks for your name, age, and gender, then returns them to you
"""

import telegram
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters
import os


API_KEY = os.getenv("TELEGRAM_DUMMY_API")

# Need to let Telegram know what code to run using API_KEY. Set using updater
updater = Updater(API_KEY)
dispatcher = updater.dispatcher

# Storing data about every human first
human_dict = {}

# Storing different states
FIRSTSTEP = 0
SECONDSTEP = 1
THIRDSTEP = 2


class Human:

    def __init__(self, name):
        self.name = name
        self.age = 0
        self.gender = ""


# The entry function
def start(update_obj: telegram.Update, context):
    update_obj.message.reply_text("Hello there, welcome to the bot! What's your name?")
    return FIRSTSTEP


# Asks for user's age
# Note that the first steps here are storing the message that was sent before this
# That is: We're grabbing the name that the user has provided, and storing it!
def ask_age_step(update_obj: telegram.Update, context):
    chat_id = update_obj.message.chat_id
    name = update_obj.message.text
    human_dict[chat_id] = Human(name)
    update_obj.message.reply_text(f"Name recorded: {name}")
    update_obj.message.reply_text("Thank you! How old are you?")
    return SECONDSTEP


# Asks for user's gender
def ask_gender_step(update_obj: telegram.Update, context):
    chat_id = update_obj.message.chat_id
    age = update_obj.message.text
    user = human_dict[chat_id]
    user.age = age
    update_obj.message.reply_text(f"Age recorded: {age}")

    # Since there are only two possible options for gender, we use a Keyboard
    gender_buttons_list = [[telegram.KeyboardButton(text="Male")], [telegram.KeyboardButton(text="Female")],
                           [telegram.KeyboardButton(text="Other")]]
    keyboard_markup = telegram.ReplyKeyboardMarkup(keyboard=gender_buttons_list, resize_keyboard=True,
                                                   one_time_keyboard=True)

    update_obj.message.reply_text("What is your gender?", reply_markup=keyboard_markup)
    return THIRDSTEP


# Stores user's gender
# This is why we need the keyboard: Setup step
def reply_user_info(update_obj: telegram.Update, context):
    chat_id = update_obj.message.chat_id
    gender = update_obj.message.text
    user = human_dict[chat_id]
    user.gender = gender
    update_obj.message.reply_text("Thank you!")
    update_obj.message.reply_text(output_human_info(user))
    return ConversationHandler.END


# Returns all human info as a string
def output_human_info(human: Human):
    info = f"Name: {human.name}\nAge: {human.age}\nGender: {human.gender}"
    return info


def main():

    # Introducing a Conversation Handler
    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRSTSTEP: [MessageHandler(Filters.text, ask_age_step)],
            SECONDSTEP: [MessageHandler(Filters.text, ask_gender_step)],
            THIRDSTEP: [MessageHandler(Filters.text, reply_user_info)]
        },
        fallbacks=[],
    )

    # Add the conversation handler to the dispatcher
    # This ensures that when the bot is run, all the relevant functions are present
    global dispatcher
    dispatcher.add_handler(handler)

    # Way to access the bot via the internet
    updater.start_polling()

    # Tells bot to wait for input
    updater.idle()


if __name__ == "__main__":
    main()
