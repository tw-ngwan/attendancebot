"""This file contains a few of the functions that will be used by main"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from ask_user_preferences_backend import _ask_news_sources, _ask_num_articles
from state_variables import *


# Entry function
def start(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Hello there, welcome to the NewsBot! This bot will provide you with news articles "
                                  "from various sources to keep you updated at all times! Without further ado, let's "
                                  "start configuring your preferences!")
    # Gets the news sources that user wants to get news from
    _ask_news_sources(update_obj, context)
    return FIRST


# Update's all of user's preferences
def update_preferences(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Let's update your preferences.")
    _ask_news_sources(update_obj, context)
    return FIRST


# Updates news sources specifically
def update_news(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Ah, of course, the news.")
    _ask_news_sources(update_obj, context)
    return FIRST


# Update articles and timing specifically
def update_timing(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Timings! Let's go ahead and change your specified frequency!")
    _ask_num_articles(update_obj, context)
    return SECOND


# Sends user help
def user_help(update_obj: Update, context: CallbackContext) -> int:
    help_message = """Use the following commands to navigate the bot: 
    /start - set up 
    /update - update all your preferences
    /updatenews - update news sources you want 
    /updatetiming - update when you want to receive news sources
    /help - find the function you need 
    /exit - exits a currently running function 
    /quit - quits the bot """
    update_obj.message.reply_text(help_message)
    return ConversationHandler.END


# Exits a currently running function
def exit_function(update_obj: Update, context: CallbackContext):
    update_obj.message.reply_text("Exiting function")
    return ConversationHandler.END


# Quits running of the bot
def quit_bot(update_obj: Update, context: CallbackContext):
    update_obj.message.reply_text("So sad to see you go! :(")
    return ConversationHandler.END
