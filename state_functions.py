"""
This file contains a few functions that changes the state of the object. Functions will be used by main

Things to ask user:
Which news agencies do they want to receive news from (Keyboard)
How many articles does user want to receive a day? (1-50)
How frequently does user want to receive messages? (Once a day to twenty times a day)
What times do the user want to receive messages at? (Let user select at 30-minute intervals)

Personal note: I feel that get_message_times is a bit unnecessary. I won't implement it first

"""

from telegram import Update
from telegram.ext import CallbackContext
from state_variables import *
from ask_user_preferences_backend import _ask_num_articles, _ask_frequency
from telegram.ext import ConversationHandler


# Gets which group is entered


# Asks users for which news sources they want
def get_news_sources(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    # The actual implementation needs to be further researched. This is a placeholder first
    news_sources = list(update_obj.message.text)
    # Not actual implementation
    _store_preferences('news', news_sources, chat_id)
    update_obj.message.reply_text("News sources recorded.")
    _ask_num_articles(update_obj, context)
    return SECOND


# Asks users for number of articles per day
def get_num_articles(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    num_articles = int(update_obj.message.text)
    # Not actual implementation
    _store_preferences('num_articles', num_articles, chat_id)
    update_obj.message.reply_text("Number of articles recorded.")
    _ask_frequency(update_obj, context)
    return THIRD


# Asks users for frequency of news articles
def get_frequency(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    frequency = int(update_obj.message.text)
    # Not actual implemenation
    _store_preferences('frequency', frequency, chat_id)
    update_obj.message.reply_text("Frequency recorded.")
    update_obj.message.reply_text("Thank you for using NewsBot! You will be getting your first update shortly.")
    return ConversationHandler.END


# Asks users for what timings they want to receive messages at
def get_message_times(update_obj: Update, context: CallbackContext) -> int:
    pass


# Updates news sources specifically
def get_news_sources_specific(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    # The actual implementation needs to be further researched. This is a placeholder first
    news_sources = list(update_obj.message.text)
    # Not actual implementation
    _store_preferences('news', news_sources, chat_id)
    update_obj.message.reply_text("News sources recorded.")
    return ConversationHandler.END


# This is a shell function for storing user preferences. It is NOT to be used, and actual implementation with
# SQLite should be implemented
def _store_preferences(parameter, state, chat_id) -> None:
    pass
