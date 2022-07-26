"""Asks for user preferences; thereby implementing the backend for some state functions and entry functions"""

# from keyboards import *
from telegram import Update
from telegram.ext import CallbackContext
from string import ascii_uppercase, ascii_lowercase, digits
import random
import sqlite3
import itertools
import shelve


# Generates a random password
def generate_random_password(length=12, iterations=1) -> list[str]:
    return [''.join([random.choice(''.join([ascii_uppercase, ascii_lowercase, digits])) for _ in range(length)])
            for _ in range(iterations)]


# Generates a random, unique group code
def generate_random_group_code() -> str:
    # How this works:
    # I have a database of 100,000 group codes stored in a database (shelve), along with the current_group_number
    # Whenever a new group is created, the next group code in line will be used, to ensure that it remains unique.
    # Thus, this allows for O(1) lookup and generation of the group code
    with shelve.open('groups.db') as s:
        group_code = s['group_codes'][s['current_group']]
        s['current_group'] += 1
    return group_code


# Gets the user's reply
def get_admin_reply(update_obj: Update, context: CallbackContext):
    chat_id = update_obj.message.chat_id
    message = update_obj.message.text.strip()
    return chat_id, message


# Gets the groups that an admin is in
# Returns list of tuples: (group_name, group_id, role)
def get_admin_groups(chat_id):
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT groups.Name, admins.group_id, admins.role
              FROM admins
              JOIN groups 
                ON admins.group_id = groups.id 
             WHERE admins.chat_id = ?
            """,
            (chat_id, )
        )
        user_groups = cur.fetchall()

        # Save changes
        con.commit()

    # user_groups is a list of tuples, where each tuple is of the form (Group Name, Group ID, Role)
    return user_groups


# Gets all the group members of a group
# Returns list of tuples: (group_id, group_name)
def get_group_members(group_id):
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, Name FROM users
             WHERE group_id = ?
            """,
            (group_id, )
        )
        all_ids = cur.fetchall()
    return all_ids


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
