"""A list of keyboards that can be used across functions"""

from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from state_variables import MAX_ARTICLES, MAX_FREQUENCY

# Keyboard for selecting news sources
# Note that this is an arbitrary list, we may not be going with this
# Need to find a way to implement so that users can select a list of options. To be added
potential_news_sources = ["Reuters", "Agence France-Presse (AFP)", "BBC", "Guardian", "New York Times",
                          "Washington Times", "Wall Street Journal", "Vox", "Telegraph", "Financial Times"]
# This will be used to check if a news source is selected and should be used
news_sources_selected = {source: 0 for source in potential_news_sources}
news_sources_button_list = [[InlineKeyboardButton(text=source, callback_data=i)]
                            for i, source in enumerate(potential_news_sources)]
# Adding Done button where something would be done
news_sources_button_list.append([InlineKeyboardButton(text="Done", callback_data=len(potential_news_sources))])
news_sources_keyboard_markup = InlineKeyboardMarkup(inline_keyboard=news_sources_button_list, resize_keyboard=True,
                                                    one_time_keyboard=True)
# To resolve the list implementation issue: The following links may help
# https://github.com/php-telegram-bot/core/issues/307
# https://stackoverflow.com/questions/70270239/python-telegram-bot-how-to-allow-for-multiple-callbackdata-when-using-inlinekeyb
# https://towardsdatascience.com/bring-your-telegram-chatbot-to-the-next-level-c771ec7d31e4
# '✔'

# Keyboard for selecting number of news sources
num_articles_button_list = [[KeyboardButton(text=str(i))] for i in range(1, MAX_ARTICLES + 1)]
num_articles_keyboard_markup = ReplyKeyboardMarkup(keyboard=num_articles_button_list, resize_keyboard=True,
                                                   one_time_keyboard=True)

# Keyboard for getting frequency for receiving messages
frequency_button_list = [[KeyboardButton(text=str(i))] for i in range(1, MAX_FREQUENCY + 1)]
frequency_keyboard_markup = ReplyKeyboardMarkup(keyboard=frequency_button_list, resize_keyboard=True,
                                                one_time_keyboard=True)

# Fake keyboard for trial
fake_news_keyboard_button_list = [[KeyboardButton(text="Test")], [KeyboardButton(text="Trial")]]
fake_news_keyboard_markup = ReplyKeyboardMarkup(keyboard=fake_news_keyboard_button_list, resize_keyboard=True,
                                                one_time_keyboard=True)
