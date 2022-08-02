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
                                  "Please key in /help for a list of useful functions, or if you want to get a full "
                                  "list of functions, type /helpfull. Else, create your first group now with "
                                  "/creategroup, or join a group with /joingroup! "
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

    return ConversationHandler.END


# Sends user help
def user_help(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text(settings.help_message)
    return ConversationHandler.END


# Sends user the full help message
def user_help_full(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text(settings.full_help_message)
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
