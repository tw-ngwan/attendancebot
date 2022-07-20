"""
This file contains a few functions that changes the state of the object. Functions will be used by main

"""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
import settings
from keyboards import groups_button_markup


# Gets new group title
def name_group_title(update_obj: Update, context: CallbackContext) -> int:
    chat_id, title = _get_user_reply(update_obj, context)
    # Do something to store the title in SQLite
    update_obj.message.reply_text(f"Ok, your group will be named {title}")
    return settings.SECOND


# Enters a group
def enter_group_implementation(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id, title = _get_user_reply(update_obj, context)
    # Verify that that group exists first, then enter. Use SQLite to pull groups that user is part of.
    settings.current_group = title
    update_obj.message.reply_text(f"Ok, you have entered {title}")
    return ConversationHandler.END


# Asks users for which news sources they want
def get_news_sources(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    # The actual implementation needs to be further researched. This is a placeholder first
    news_sources = list(update_obj.message.text)
    # Not actual implementation
    _store_preferences('news', news_sources, chat_id)
    update_obj.message.reply_text("News sources recorded.")
    # _ask_num_articles(update_obj, context)
    return settings.SECOND


# Asks users for number of articles per day
def get_num_articles(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    num_articles = int(update_obj.message.text)
    # Not actual implementation
    _store_preferences('num_articles', num_articles, chat_id)
    update_obj.message.reply_text("Number of articles recorded.")
    # _ask_frequency(update_obj, context)
    return settings.THIRD


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


# Gets the user's reply
def _get_user_reply(update_obj: Update, context: CallbackContext):
    chat_id = update_obj.message.chat_id
    message = update_obj.message.text.strip()
    return chat_id, message


# This is a shell function for storing user preferences. It is NOT to be used, and actual implementation with
# SQLite should be implemented
def _store_preferences(parameter, state, chat_id) -> None:
    pass
