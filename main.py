"""
Newsbot: This is the implementation of the full bot
Code for state functions and entry_functions are stored in separate files

The bot sends the user a message at certain specific times. The message’s contents will be links to news articles.
"""


import os
from entry_functions import start, update_preferences, update_news, update_timing, user_help, exit_function, quit_bot
from state_variables import *
from state_functions import get_news_sources, get_num_articles, get_frequency, get_news_sources_specific
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters


API_KEY = os.getenv("TELEGRAM_API")

# Letting Telegram know which bot to run code on
updater = Updater(API_KEY)
dispatcher = updater.dispatcher

# Checking that all libraries have been loaded, function can start
print("Bot starting...")


# Main function
def main():

    # Introducing the necessary conversation handlers
    # Start handler handles update, timings_update as well
    start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('update', update_preferences),
                      CommandHandler('updatetiming', update_timing)],
        states={
            FIRST: [MessageHandler(Filters.text, get_news_sources)],
            SECOND: [MessageHandler(Filters.text, get_num_articles)],
            THIRD: [MessageHandler(Filters.text, get_frequency)],

        },
        fallbacks=[]
    )
    news_update_handler = ConversationHandler(
        entry_points=[CommandHandler('updatenews', update_news)],
        states={
            FIRST: [MessageHandler(Filters.text, get_news_sources_specific)]
        },
        fallbacks=[])
    help_handler = ConversationHandler(entry_points=[CommandHandler('help', user_help)], states={}, fallbacks=[])
    exit_handler = ConversationHandler(entry_points=[CommandHandler('exit', exit_function)], states={}, fallbacks=[])
    quit_handler = ConversationHandler(entry_points=[CommandHandler('quit', quit_bot)], states={}, fallbacks=[])

    # Adds the conversation handlers to the dispatchers
    global dispatcher
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(news_update_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(exit_handler)
    dispatcher.add_handler(quit_handler)

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
