"""This file contains a few of the help functions that will be used by main"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, Defaults
import settings
import datetime
from dateutil import tz
from backend_implementations import get_day_group_attendance, get_admin_reply
from developer_functions import get_all_developer_chat_ids
from entry_group_functions import create_group, get_group_passwords, join_existing_group, enter_group
from state_group_functions import create_group_follow_up, set_username, join_group_get_group_code, \
    join_group_follow_up, enter_group_follow_up
from entry_user_functions import add_users
from state_user_functions import add_user_follow_up
from entry_attendance_functions import get_today_group_attendance, get_tomorrow_group_attendance, \
    get_any_day_group_attendance, change_attendance, change_any_day_attendance
from state_attendance_functions import change_today_attendance_follow_up, get_specific_day_group_attendance_follow_up
import psycopg2
from data import DATABASE_URL


"""
TypeError: Only timezones from the pytz library are supported
Resolution is to set tzinfo==2.1 in requirements.txt. Check to reorder again, possibly institute a setup.py
"""


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

    # This NEEDS to be updated. You need to check what groups user is in, then run this
    # Also you need a setting to see if the user wants to be active or not
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
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT group_id 
                  FROM admins
                 WHERE chat_id = %s::TEXT""", (chat_id, )
            )
            parsed_info = cur.fetchall()
            group_ids = [group_id[0] for group_id in parsed_info]

    print(group_ids)
    return group_ids


# For users to send feedback
def feedback(update_obj: Update, context: CallbackContext):
    update_obj.message.reply_text("Send the feedback message that you want to give to the developers here")
    return settings.FIRST


# Follow up on feedback function
def feedback_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    username = update_obj.message.from_user.username
    developer_ids = get_all_developer_chat_ids()  # This one you may want to change
    try:
        for developer in developer_ids:
            context.bot.send_message(chat_id=developer, text=f"Feedback from {username} (chat id: {chat_id}):")
            context.bot.send_message(chat_id=developer, text=message)
    except Exception as e:
        update_obj.message.reply_text("Sorry, there has been an issue... Your feedback can't get through "
                                      "for now, please try again later!")
        print(str(e))
        return ConversationHandler.END
    else:
        update_obj.message.reply_text("Your feedback has been sent to the developers. Thank you!")
        return ConversationHandler.END


# Tutorial functions: This will be long
def tutorial(update_obj: Update, context: CallbackContext):
    update_obj.message.reply_text("Welcome to the tutorial! Let's get you started, shall we? ")
    update_obj.message.reply_text("The bot tracks attendance and events in the format of groups of users. "
                                  "Let's start by creating a group! Call the /creategroup function, and follow "
                                  "the instructions given!")
    update_obj.message.reply_text("To break out of the tutorial at any time, send OK")
    return settings.FIRST


def tutorial_create_group(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip() != '/creategroup':
        update_obj.message.reply_text("Create a group first with /creategroup!")
        return settings.FIRST

    create_group(update_obj, context)
    update_obj.message.reply_text("Let's name the group 'Trial Group'! Set your group name now!")
    return settings.SECOND


def tutorial_create_group_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != 'trial group':
        update_obj.message.reply_text("Name your group 'Trial Group!' (without the ')")
        return settings.SECOND
    create_group_follow_up(update_obj, context)
    return settings.THIRD


def tutorial_create_group_set_username_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    set_username(update_obj, context)
    update_obj.message.reply_text("Great, you have set your username! Now, let's start by adding users into the "
                                  "group. Users are just people whose attendance will be tracked. "
                                  "Without further ado, let's go! Type /addusers to start")
    update_obj.message.reply_text("Note: If you received a message saying that you failed to set your username, please "
                                  "set your username again. Type /setusername to set it again! Do NOT go to add users")
    return settings.FOURTH


def tutorial_add_users_or_add_username(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip() == '/setusername':
        update_obj.message.reply_text("Type your username into the chat")
        return settings.THIRD  # Goes back to the previous state
    if message.strip() != '/addusers':
        update_obj.message.reply_text("Add users first with /addusers!")
        return settings.FOURTH
    user_added = add_users(update_obj, context)
    # This means that you have not set your username, because it means ConversationHandler.END returned
    if user_added < 0:
        update_obj.message.reply_text("You have not set your username yet! Type /setusername to set it first!")
        return settings.FOURTH

    update_obj.message.reply_text("Great! Now, let's add our first user, Adam. Type Adam into the chat")
    return settings.FIFTH


def tutorial_add_users_add_adam(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != 'adam':
        update_obj.message.reply_text("Add Adam into the chat first!")
        return settings.FIFTH
    add_user_follow_up(update_obj, context)
    update_obj.message.reply_text("Great! Now, let's add our second user, Grace. Type Grace into the chat")
    return settings.SIXTH


def tutorial_add_users_add_grace(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != 'grace':
        update_obj.message.reply_text("Add Grace into the chat first!")
        return settings.SIXTH
    add_user_follow_up(update_obj, context)
    update_obj.message.reply_text("Great! Now, let's add our third user, Eve. Type Eve into the chat")
    return settings.SEVENTH


def tutorial_add_users_add_eve(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != 'eve':
        update_obj.message.reply_text("Add Eve into the chat first!")
        return settings.SEVENTH
    add_user_follow_up(update_obj, context)
    update_obj.message.reply_text("Great! We've now added all the users we want. Type OK into the chat to end")
    return settings.EIGHTH


def tutorial_end_add_users(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() != 'ok':
        update_obj.message.reply_text("Type OK into the chat to end adding users!")
        return settings.EIGHTH
    add_user_follow_up(update_obj, context)
    update_obj.message.reply_text("Great! Now that we've added all the users we want, let's try getting today's "
                                  "attendance. To do so, type /get into the chat")
    return settings.NINTH


def tutorial_get_attendance(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/get':
        update_obj.message.reply_text("Get today's attendance first with /get!")
        return settings.NINTH
    get_today_group_attendance(update_obj, context)
    update_obj.message.reply_text("Great! We've gotten today's attendance! Let's try getting tomorrow's attendance "
                                  "now. To do so, type /gettmr into the chat")
    return settings.TENTH


def tutorial_get_tmr_attendance(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/gettmr':
        update_obj.message.reply_text("Get tomorrow's attendance first with /gettmr!")
        return settings.TENTH
    get_tomorrow_group_attendance(update_obj, context)
    update_obj.message.reply_text("Great! We've gotten tomorrow's attendance! Now, let's try to actually change the "
                                  "attendance for today. To do so, type /change into the chat")
    return settings.ELEVENTH


def tutorial_change_today_attendance(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/change':
        update_obj.message.reply_text("Change today's attendance first with /change!")
        return settings.ELEVENTH
    change_attendance(update_obj, context)
    update_obj.message.reply_text("Great! Let's try and change attendance based on the formats shown. Let's say Adam "
                                  "is on leave, Grace is taking PM OFF. Change the attendance by sending this!")
    update_obj.message.reply_text("1: LL\n2: P / OFF")
    return settings.TWELFTH


def tutorial_change_today_attendance_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    message_list = [att.split(':') for att in message.strip().split('\n')]
    message_list = [a.strip() for r in message_list for a in r]
    if len(message_list) == 4:
        message_list[3] = [r.strip() for r in message_list[3].split('/')]
        if len(message_list[3]) != 2:
            update_obj.message.reply_text("Change the attendance to what was sent in the message!")
            update_obj.message.reply_text("1: LL\n2: P / OFF")
            return settings.TWELFTH
        if message_list[0].lower() == '1' and message_list[1].lower() == 'll' and message_list[2].lower() == '2' \
            and message_list[3][0].lower() == 'p' and message_list[3][1].lower() == 'off':
            change_today_attendance_follow_up(update_obj, context)
            update_obj.message.reply_text("Great! You've changed today's attendance! We can confirm this by calling "
                                          "/get once again. Let's do that!")
            return settings.THIRTEENTH

    update_obj.message.reply_text("Change the attendance to what was sent in the message!")
    update_obj.message.reply_text("1: LL\n2: P / OFF")
    return settings.TWELFTH


def tutorial_get_attendance_after_change(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/get':
        update_obj.message.reply_text("Get today's attendance first with /get!")
        return settings.THIRTEENTH

    get_today_group_attendance(update_obj, context)
    update_obj.message.reply_text("Great! We can also change tomorrow's attendance with /changetmr, but let's not try "
                                  "that for now (it works the same as /change). What if we wanted to get the "
                                  "attendance of any day? We can do so with /getany. Let's try that now!")
    return settings.FOURTEENTH


def tutorial_get_any_day_attendance(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/getany':
        update_obj.message.reply_text("Get the attendance first with /getany!")
        return settings.FOURTEENTH

    get_any_day_group_attendance(update_obj, context)
    update_obj.message.reply_text("Great! Let's try to get the attendance for 011122. Follow the instructions, and "
                                  "type 011122 into the chat!")
    return settings.FIFTEENTH


def tutorial_get_any_day_attendance_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip() != '011122':
        update_obj.message.reply_text("Type 011122 into the chat to get the attendance for that day!")
        return settings.FIFTEENTH

    get_specific_day_group_attendance_follow_up(update_obj, context)
    update_obj.message.reply_text("Great! This is how you can get the attendance for any day! To change the attendance "
                                  "of any day, we can call /changeany, and then likewise, type in the date, but we "
                                  "aren't going to try that now. ")
    update_obj.message.reply_text("But how are we going to be able to join groups that have already been created? "
                                  "We can use the /joingroup function, to join a group that already exists! Groups are "
                                  "identified by their group codes and passwords, which will allow other users to join "
                                  "groups that have already been created. Let's try getting our group's codes with "
                                  "/getgroupcodes!")
    return settings.SIXTEENTH


def tutorial_get_group_codes(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/getgroupcodes':
        update_obj.message.reply_text("Get your group's codes first with /getgroupcodes!")
        return settings.SIXTEENTH

    get_group_passwords(update_obj, context)
    update_obj.message.reply_text("Great! These are your group's codes and passwords! The first 8-letter code is a "
                                  "unique code that identifies your group. The other 3 messages are the Observer, "
                                  "Member, and Admin passwords respectively. ")
    update_obj.message.reply_text("But what do we mean by Admins, Members, and Observers? These are the three security "
                                  "tiers present (in descending order). Admins have the most power over the group, "
                                  "able to do anything up to deleting the group. Members can change and get attendance,"
                                  " but are restricted from doing anything too powerful. Observers cannot enact any "
                                  "changes, but can only watch the group. As the creator of the group, you are "
                                  "automatically an Admin. ")
    update_obj.message.reply_text("How do these come into play? Let's find out, by joining a group that has already "
                                  "been created! Use the /joingroup function")
    return settings.SEVENTEENTH


def tutorial_join_group(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/joingroup':
        update_obj.message.reply_text("Join a group first with /joingroup!")
        return settings.SEVENTEENTH

    join_existing_group(update_obj, context)
    update_obj.message.reply_text("Great! Let's use the following group code (copy and send the next message)")
    update_obj.message.reply_text("VDIZZPOA")
    return settings.EIGHTEENTH


def tutorial_join_group_get_group_codes(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().upper() != "VDIZZPOA":
        update_obj.message.reply_text("Join the group by sending the group code!")
        update_obj.message.reply_text("VDIZZPOA")
        return settings.EIGHTEENTH

    join_group_get_group_code(update_obj, context)
    update_obj.message.reply_text("Great! Now, let's use the following password to enter the group (copy and send the "
                                  "next message)")
    update_obj.message.reply_text("i1FZfFfAS24m")
    return settings.NINETEENTH


def tutorial_join_group_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip() != "i1FZfFfAS24m":
        update_obj.message.reply_text("Verify yourself by sending the correct password!")
        update_obj.message.reply_text("i1FZfFfAS24m")
        return settings.NINETEENTH

    join_group_follow_up(update_obj, context)
    update_obj.message.reply_text("Congratulations! You are now inside the group! Set your username now")
    return settings.TWENTIETH


def tutorial_join_group_set_username(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    set_username(update_obj, context)
    update_obj.message.reply_text("Great, you have set your username! Let's try getting attendance to see what happens."
                                  " Use /get")
    update_obj.message.reply_text("Note: If you received a message saying that you failed to set your username, please "
                                  "set your username again. Type /setusername to set it again! Do NOT go to add users")
    return settings.TWENTYFIRST


def tutorial_join_new_group_get_attendance(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() == '/setusername':
        update_obj.message.reply_text("Type your username into the chat")
        return settings.TWENTIETH
    if message.strip().lower() != '/get':
        update_obj.message.reply_text("Get attendance first with /get!")
        return settings.TWENTYFIRST

    get_today_group_attendance(update_obj, context)

    update_obj.message.reply_text("Congratulations! Let's try changing attendance now. Use /change")
    return settings.TWENTYSECOND


def tutorial_new_group_change_attendance_fail(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/change':
        update_obj.message.reply_text("Try changing attendance first with /change!")
        return settings.TWENTYSECOND

    change_attendance(update_obj, context)
    update_obj.message.reply_text("See? You need to be a Member to change attendance. As an Observer, you don't "
                                  "have the privileges to do so. This is how the different group codes can help to "
                                  "differentiate between users and ensure security of your group. To become a Member, "
                                  "you can call /uprank and enter the member password, but we're not going to "
                                  "do that. ")
    update_obj.message.reply_text("Let's say we want to get the attendance of our Trial Group just now. We can do that "
                                  "by now entering that group. Use /enter to go back into the Trial Group!")
    return settings.TWENTYTHIRD


def tutorial_enter_group(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/enter':
        update_obj.message.reply_text("Enter the group first with /enter!")
        return settings.TWENTYTHIRD

    enter_group(update_obj, context)
    update_obj.message.reply_text("Choose your Trial Group (select the button with that group)")
    return settings.TWENTYFOURTH


def tutorial_enter_group_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if 'trial group' not in message.strip().lower():
        update_obj.message.reply_text("Select the correct group!")
        return settings.TWENTYFOURTH

    enter_group_follow_up(update_obj, context)
    update_obj.message.reply_text("Well done. To verify that you've entered the correct group, type /get once again")
    return settings.TWENTYFIFTH


def tutorial_enter_group_get_attendance(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Exiting tutorial...")
        return ConversationHandler.END
    if message.strip().lower() != '/get':
        update_obj.message.reply_text("Get the attendance of your group with /get!")
        return settings.TWENTYFIFTH

    get_today_group_attendance(update_obj, context)
    update_obj.message.reply_text("Well done! We have so many other functions we want to show you, but there's "
                                  "no time for that. To get a list of helpful functions, type /help. To get a "
                                  "full list of functions that we have, type /helpfull. ")
    update_obj.message.reply_text("Good job! You have come to the end of the tutorial. Another potentially useful "
                                  "function that you may want to use is /getgrouphistory, which gets the history of "
                                  "everything that's been done in the group. This helps you to track who has done "
                                  "which changes, in case anything goes wrong. We also allow for parent group "
                                  "functionality, which can be called using the /mergegroups function. This helps "
                                  "you to get multiple child groups' attendance at once, by just calling for the "
                                  "attendance of the parent group (eg: A battalion group can have multiple company "
                                  "groups as their children, merged using /mergegroups, which themselves can have "
                                  "multiple platoon groups). ")
    update_obj.message.reply_text("Feel free to continue to play around and explore the bot! To replay the tutorial, "
                                  "type /tutorial. To send feedback to the developer, type /feedback. See you around!")
    return ConversationHandler.END
