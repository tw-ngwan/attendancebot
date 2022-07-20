"""Asks for user preferences; thereby implementing the backend for some state functions and entry functions"""

from keyboards import *
from telegram import Update
from telegram.ext import CallbackContext
from string import ascii_uppercase, ascii_lowercase, digits
import random


# Generates a random password
def generate_random_password(password=True, length=12, iterations=1) -> list[str]:
    # If want to generate group code instead
    if not password:
        group_code_length = 8
        return [''.join([random.choice(ascii_uppercase) for _ in range(group_code_length)])]

    return [''.join([random.choice(''.join([ascii_uppercase, ascii_lowercase, digits])) for _ in range(length)])
            for _ in range(iterations)]


def _start_broadcasting_attendance():
    pass


# # Asks for user's news sources preferences
# def _ask_news_sources(update_obj: Update, context: CallbackContext) -> None:
#     # Gets the news sources that user wants to get news from
#     update_obj.message.reply_text("What news sources do you want to get your news from?",
#                                   reply_markup=fake_news_keyboard_markup)
#     # update_obj.message.reply_text("What news sources do you want to get your news from?",
#     #                               reply_markup=news_sources_keyboard_markup)
#
#
# # Asks for user's preferred number of articles
# def _ask_num_articles(update_obj: Update, context: CallbackContext) -> None:
#     update_obj.message.reply_text("How many articles do you want to get a day?",
#                                   reply_markup=num_articles_keyboard_markup)
#
#
# # Asks for frequency of getting articles
# def _ask_frequency(update_obj: Update, context: CallbackContext) -> None:
#     update_obj.message.reply_text("How often do you want to receive a message?",
#                                   reply_markup=frequency_keyboard_markup)
