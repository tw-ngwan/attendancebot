"""Stores events. Events are activities that members across groups can participate in. Stuff like IPPT, MFT for eg"""
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
from backend_implementations import verify_group_and_role
import datetime


# Tracks the start of an event
def start_event(update_obj: Update, context: CallbackContext):

    # Must be a member to start an event, at least
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    update_obj.message.reply_text("Select an event to join, or join a new event, or participate in a new event "
                                  "with the event code")
    return settings.FIRST




