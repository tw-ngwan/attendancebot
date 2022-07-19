from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from ask_user_preferences_backend import _ask_news_sources, _ask_num_articles
from state_variables import *


# Creates a group
def create_group(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Great! What would you like to name your group? To cancel, type 'OK'")
    return FIRST


# Enters group
def enter_group(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Which group would you like to enter?")
    return FIRST
    pass


# Gets the current group
def current_group(update_obj: Update, context: CallbackContext) -> int:
    pass


# Update's all of user's preferences
def update_preferences(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Let's update your preferences.")
    _ask_news_sources(update_obj, context)
    return FIRST
