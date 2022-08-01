"""This file contains a few of the help functions that will be used by main"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, Defaults
import settings
import sqlite3
import datetime
from dateutil import tz
from backend_implementations import get_day_group_attendance


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

    # Starts running the repeated functions daily:
    # Sends today's attendance at 6am, tomorrow's attendance at 2pm and 9pm
    context.job_queue.run_daily(get_today_attendance, time=datetime.time(hour=6, minute=0, tzinfo=SGT),
                                context=update_obj.message.chat_id)
    context.job_queue.run_daily(get_tomorrow_attendance, time=datetime.time(hour=14, minute=0, tzinfo=SGT),
                                context=update_obj.message.chat_id)
    context.job_queue.run_daily(get_tomorrow_attendance, time=datetime.time(hour=21, minute=0, tzinfo=SGT),
                                context=update_obj.message.chat_id)
    # context.job_queue.run_repeating(get_today_attendance, interval=10, first=10, context=update_obj.message.chat_id)
    # context.job_queue.run_repeating(get_today_attendance, interval=8, first=20, context=update_obj.message.chat_id)

    return ConversationHandler.END


# Gets today's attendance and sends it
def get_today_attendance(context: CallbackContext):
    # First, we get the groups that the user is in
    group_ids = get_admin_groups(context)
    today = datetime.date.today()
    while today.weekday() > 4:
        today += datetime.timedelta(days=1)

    # Next, we get the group attendance for each of the groups
    for group_id in group_ids:
        get_day_group_attendance(context, today, group_id)


# Gets tomorrow's attendance and sends it
def get_tomorrow_attendance(context: CallbackContext):
    # First, we get the groups that the user is in
    group_ids = get_admin_groups(context)
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    while tomorrow.weekday() > 4:
        tomorrow += datetime.timedelta(days=1)

    # We get the group attendance for each of the groups
    for group_id in group_ids:
        get_day_group_attendance(context, tomorrow, group_id)


# Gets the groups that the user is in
def get_admin_groups(context: CallbackContext):
    chat_id = context.job.context
    # We use sqlite to get the groups that the user is in
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT group_id 
              FROM admins
             WHERE chat_id = ?""", (chat_id, )
        )
        parsed_info = cur.fetchall()
        group_ids = [group_id[0] for group_id in parsed_info]

    print(group_ids)
    return group_ids


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
# Ok don't do this. Only update the attendance of the next day
# And in fact I think we don't need this function
# Here's what I will do: When the bot sends the next day's attendance, it will parse the table to look for members
# and whether their attendance has been updated. If the answer is yes, display as such. If no, then display as P,
# and update the members' attendance as P in the attendance database.
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
