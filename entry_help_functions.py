"""This file contains a few of the help functions that will be used by main"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings


# Entry function
def start(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
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
    return ConversationHandler.END


"https://stackoverflow.com/questions/59611662/how-to-send-message-from-bot-to-user-at-a-fixed-time-or-at-intervals-through-pyt"
"How to let the bot prompt the user every day, run function repeatedly. "


# Sends user help
def user_help(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text(settings.help_message)
    return ConversationHandler.END
