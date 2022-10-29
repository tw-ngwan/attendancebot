"""A list of keyboards that can be used across functions"""

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from backend_implementations import get_admin_groups, get_past_group_events, get_current_group_events, \
    get_all_past_group_events_with_timestamp, get_time_string_from_datetime


# Button list for users to indicate boolean variables
yes_no_button_list = [[KeyboardButton(text="Yes")], [KeyboardButton(text="No")]]
yes_no_button_markup = ReplyKeyboardMarkup(keyboard=yes_no_button_list, resize_keyboard=True,
                                           one_time_keyboard=True)


# Gets a KeyboardMarkup of all group names
# Each group name comprises of '{group_name} ({group_id})'. This enables me to get the group_id to update the settings.
def group_name_keyboards(chat_id, extra_options=None):
    if extra_options is None:
        extra_options = []
    user_groups = get_admin_groups(chat_id)
    group_names = [[''.join([group[0], ' (', str(group[3]), ')'])] for group in user_groups]
    # Adds the other options in extra_options
    for option in extra_options:
        group_names.append([option])
    groups_button_markup = ReplyKeyboardMarkup(keyboard=group_names, resize_keyboard=True,
                                               one_time_keyboard=True)
    return groups_button_markup


# Keyboard that lists all events that a group has joined before. Or current events, if you set current=True
def events_keyboards(group_id, extra_options=None, current=False):
    if extra_options is None:
        extra_options = []

    group_events = get_past_group_events(group_id) if not current else get_current_group_events(group_id)
    group_events_names = [[f"{event[0]} ({event[1]})"] for event in group_events]
    for option in extra_options:
        group_events_names.append([option])
    group_events_button_markup = ReplyKeyboardMarkup(keyboard=group_events_names, resize_keyboard=True,
                                                     one_time_keyboard=True)
    return group_events_button_markup


# For getting and tracking all past events
def all_past_events_keyboards(group_id, extra_options=None):
    if extra_options is None:
        extra_options = []

    group_events = get_all_past_group_events_with_timestamp(group_id)
    group_events_names = [[f"{event[0]} {get_time_string_from_datetime(event[2])} ({event[1]})"]
                          for event in group_events]
    for option in extra_options:
        group_events_names.append([option])
    group_events_button_markup = ReplyKeyboardMarkup(keyboard=group_events_names, resize_keyboard=True,
                                                     one_time_keyboard=True)
    return group_events_button_markup
