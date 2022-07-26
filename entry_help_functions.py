"""This file contains a few of the help functions that will be used by main"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, Defaults
import settings
import sqlite3
import datetime
from dateutil import tz


# Entry function
def start(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:

    # Welcomes the user, gives a short tutorial
    update_obj.message.reply_text("Hello there, welcome to the AttendanceBot!\n"
                                  "This bot will help you to track the attendance of your organization, group, or "
                                  "club! Attendance is tracked using 'groups', our method of distinguishing the "
                                  "attendance of separate groups, so that you can track multiple groups' attendance "
                                  "concurrently. \n"
                                  "Every day, this bot will update you with the attendance of all groups you are "
                                  "a part of. You can edit your attendance with /changemyattendance \n"
                                  "If this is your first time using the bot, please key in /tutorial "
                                  "for a tutorial on how to use the bot! Else, if you are just looking for a "
                                  "refresher, please type /help for all the commands you need. \n"
                                  "Create your first group now with /creategroup!"
                                  )

    # Sets the timezone
    SGT = tz.gettz('Asia/Singapore')
    Defaults.tzinfo = SGT

    # Starts running the repeated functions daily
    context.job_queue.run_daily(trial_function, time=datetime.time(hour=11, minute=39, tzinfo=SGT),
                                context=update_obj.message.chat_id)
    context.job_queue.run_repeating(trial_function_two, interval=5, first=10, context=update_obj.message.chat_id)
    # context.job_queue.run_repeating(trial_function, interval=10, first=30, context=update_obj.message.chat_id)

    return ConversationHandler.END


"https://stackoverflow.com/questions/59611662/how-to-send-message-from-bot-to-user-at-a-fixed-time-or-at-intervals-through-pyt"
"How to let the bot prompt the user every day, run function repeatedly. "
"""
Further stuff to do: 
Every day at 2pm, update attendance
Every day at 2pm, send the message for attendance of the next day. 
Track the date (how?) """


# Updates the attendance for the next day
# What I want this function to do:
# I want the attendance of the whole of next week to be recorded. So on 2pm of day 1,
# I want the attendance of day 8 to be stored in the SQLite table.
# All entries will be P
def update_attendance():

    # First, we find all the groups that need attendance updated
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT groups.id, groups.NumDailyReports, users.id
              FROM groups
              JOIN users
                ON groups.id = users.group_id
            """
        )
        user_groups = cur.fetchall()

        # Next, for each group, we update all the necessary attendances
        for group in user_groups:
            group_id, frequency, user_id = group
            for i in range(frequency):
                cur.execute(
                    """
                    INSERT INTO attendance
                    (group_id, user_id, TimePeriod, Date, AttendanceStatus)
                    VALUES 
                    (?, ?, ?, date('now', '+7 day'), P)""",
                    (group_id, user_id, i + 1)  # 1-indexed
                )


# Trial function to test repeating
def trial_function(context: CallbackContext):
    chat_id = context.job.context
    context.bot.send_message(chat_id=chat_id,
                             text="Hi, this is a trial text")
    # print("Function one is called")


# Second trial function
def trial_function_two(context: CallbackContext):
    chat_id = context.job.context
    context.bot.send_message(chat_id=chat_id,
                             text="Hi, this is the second trial text")
    # print("Function two is called")


# Sends user help
def user_help(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text(settings.help_message)
    return ConversationHandler.END
