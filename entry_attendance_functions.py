"""This file contains a few of the functions that will be used by main
Old file, change ALL functions here (just storing old NewsBot functions)"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from ask_user_preferences_backend import _ask_news_sources, _ask_num_articles
from state_variables import *
import settings


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
