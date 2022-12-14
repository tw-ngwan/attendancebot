"""Stores events. Events are activities that members across groups can participate in. Stuff like IPPT, MFT for eg"""
import psycopg2
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
from backend_implementations import get_admin_reply, verify_group_and_role, get_event_id_from_button, \
    check_valid_time, check_valid_date, generate_random_group_code, get_all_child_and_subchild_groups, \
    update_admin_movements, get_intended_users, convert_rank_to_id, get_group_events_backend, \
    get_datetime_from_time_string
from keyboards import events_keyboards, all_past_events_keyboards, ReplyKeyboardRemove
from data import DATABASE_URL
import datetime


# Gets tutorial about events and what each of the functions entail
def event_help(update_obj: Update, context: CallbackContext):
    """Gives help on what events are and how to use them"""
    help_string = "Events are fixed-time activities that can be participated in by people of multiple groups. " \
                  "To start an event, use /startevent, and define the end-time of the event. Consequently, before " \
                  "the end of the event, anyone from the group, or any of the child groups of the group, can join " \
                  "the event, and their participation, as well as time joined, will be recorded. Joining an event " \
                  "can be done with /joinevent (not to be confused with /startevent!)\n\n" \
                  "To get information on an event that's currently happening, you can use /getevent. It will show " \
                  "the names of every currently participating member in the group you are in (and all its child " \
                  "groups). To get the history of all past events, you can use /geteventhistory. \n\n" \
                  "For example, if a battalion with four companies wants to start an event (HLS, for eg), inside the " \
                  "battalion group, an Admin can run /startevent. Subsequently, members in each of the company " \
                  "groups can use /joinevent to join the event started by the battalion group. Using /getevent in " \
                  "each of the company groups will show the company's event attendance, while using /getevent in " \
                  "the battalion group will show all 4 company groups' event attendance. "
    update_obj.message.reply_text(help_string)
    return ConversationHandler.END


# Tracks the start of an event
def start_event(update_obj: Update, context: CallbackContext):

    # Must be a member to start an event, at least
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    chat_id = update_obj.message.chat_id
    current_group = settings.current_group_id[chat_id]

    update_obj.message.reply_text("Select an event to join, or create a new event",
                                  reply_markup=events_keyboards(group_id=current_group, extra_options=["New"]))
    return settings.FIRST


# Gets the event
def start_event_get_event(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)

    # If this is a new event, you need the event name
    if message.strip().lower() == 'new':
        update_obj.message.reply_text("Key in the event name. Type OK to cancel", reply_markup=ReplyKeyboardRemove())
        return settings.FOURTH

    event_id, event_name = get_event_id_from_button(message)
    if not event_id:
        update_obj.message.reply_text("Invalid event, please try again!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Stores the event name
    settings.event_tracker_storage[chat_id] = settings.Event(event_name=event_name)

    _start_event_send_get_end_time_message(update_obj, context)
    return settings.SECOND


# Gets the end time and verifies that it works
def start_event_get_end_time(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    timings = message.strip().split()
    if len(timings) > 2 or len(timings) == 0:
        update_obj.message.reply_text("Invalid date and time format!")
        return ConversationHandler.END
    if len(timings) == 2:
        timing, date = timings
    else:
        timing = timings[0]
        date = datetime.date.today()

    # Check if timing is valid
    timing = check_valid_time(timing)
    if not timing:
        update_obj.message.reply_text("Invalid time format!")
        return ConversationHandler.END

    # If date is a string, check if valid
    if type(date) == str:
        date = check_valid_date(date)
        if not date:
            update_obj.message.reply_text("Invalid date format!")
            return ConversationHandler.END

    # Timezone specified to SG Time
    event_end_time = datetime.datetime.combine(date, timing)
    now = datetime.datetime.now()
    if event_end_time < now:
        update_obj.message.reply_text("Event end time has to be after current time!")
        return ConversationHandler.END

    # Else if everything works, we store it
    settings.event_tracker_storage[chat_id].event_end = event_end_time
    update_obj.message.reply_text("Ok, end time recorded. Key in the password for users to enter the event. "
                                  "If you don't want to password protect the group, type OK")
    return settings.THIRD


# Now, it will insert the event into the
def start_event_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        password = None
    else:
        password = message.strip()

    event = settings.event_tracker_storage[chat_id]
    event.event_code = generate_random_group_code()

    current_group = settings.current_group_id[chat_id]

    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            # This gets the next serial value (so the +1; 1 table value will be omitted)
            cur.execute(
                """SELECT nextval(pg_get_serial_sequence('events', 'id')) + 1"""
            )
            event_id = cur.fetchall()
            if not event_id or event_id[0][0] is None:
                event_id = 1
            else:
                event_id = event_id[0][0]
            event.event_id = event_id

            # We get all the child and subchild groups, including the parent group
            child_groups = get_all_child_and_subchild_groups(group_id=current_group, groups=[current_group])

            # This is the argument tuple that we will use
            argument_tuple = [(event.event_id, event.event_name, event.event_end, event.event_code, password, group)
                              for group in child_groups]
            # Makes the timezone correct first
            cur.execute(
                """
                SET timezone TO 'Asia/Singapore'
                """
            )
            # Now, we add all of the events into the database. So all child groups can join the event
            cur.executemany(
                """
                INSERT INTO events
                (parent_id, event_name, DateStart, DateEnd, event_code, password, group_id) 
                VALUES 
                (%s, %s, CURRENT_TIMESTAMP(0), %s, %s, %s, %s)
                """, argument_tuple
            )

    # Update movements
    update_admin_movements(chat_id=chat_id, group_id=current_group, function='/startevent',
                           admin_text=f"Event details:\nName: {event.event_name}\nTime End: {event.event_end}")

    update_obj.message.reply_text("Your event has started. To add users, please use /joinevent. "
                                  "All members of subgroups of your group can access and join your event. "
                                  "All the best!")
    return ConversationHandler.END


# Gets the name of the new event
def start_new_event_get_name(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Ok, exiting now")
        return ConversationHandler.END

    event_name = message.strip()

    # We store the new event
    settings.event_tracker_storage[chat_id] = settings.Event(event_name=event_name)
    _start_event_send_get_end_time_message(update_obj, context)
    return settings.SECOND


# Function used by start_new_event_get_name and start_event_get_event
def _start_event_send_get_end_time_message(update_obj: Update, context: CallbackContext):
    update_obj.message.reply_text("Choose a rough end date and time, in the following format: "
                                  "<time> <date>, where time is expressed in HHMM and date in DDMMYY. If the date is "
                                  "today, then you can leave the date blank. Here's an example",
                                  reply_markup=ReplyKeyboardRemove())
    update_obj.message.reply_text("0900 141022")
    update_obj.message.reply_text("Note that the end date and time needs to be after the present")


# Allows users in group to join an event
def join_event(update_obj: Update, context: CallbackContext):

    # Verify that you are a member
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    chat_id = update_obj.message.chat_id
    current_group = settings.current_group_id[chat_id]
    update_obj.message.reply_text("Choose an event (Type OK to cancel)",
                                  reply_markup=events_keyboards(group_id=current_group, extra_options=["OK"],
                                                                current=True))
    return settings.FIRST


# Gets the event user wants to join, then prompts to verify password (if needed)
def join_event_get_password(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Ok, exiting now", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # We get the event id to join
    event_parent_id, event_name = get_event_id_from_button(message)
    if not event_parent_id:
        update_obj.message.reply_text("Invalid event, please try again!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    current_group = settings.current_group_id[chat_id]

    # Get the event_id
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT id, password
                  FROM events 
                 WHERE parent_id = %s
                   AND group_id = %s
                 ORDER BY id DESC 
                 LIMIT 1
                 """, (event_parent_id, current_group)
            )
            event_details = cur.fetchall()
            if not event_details:
                update_obj.message.reply_text("An error has occurred while retrieving group id, please try again!")
                return ConversationHandler.END
            event_id, event_password = event_details[0]

    # Store details about the event
    settings.event_joining_tracker_storage[chat_id] = settings.Event(event_id=event_id, event_name=event_name,
                                                                     event_password=event_password,
                                                                     event_parent_id=event_parent_id)

    if event_password is None:
        update_obj.message.reply_text("Type in the numbers of the users you want to add to the event, "
                                      "separated by spaces. To cancel, type 'OK'. Eg: (1 3 2)")
        return settings.THIRD
    else:
        update_obj.message.reply_text("Enter the event password (case sensitive)")
        return settings.SECOND


# Verifies if the password is correct
def join_event_verify_user_password(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip() != settings.event_joining_tracker_storage[chat_id].event_password:
        update_obj.message.reply_text("Incorrect password provided!")
        return ConversationHandler.END

    update_obj.message.reply_text("Password verified!")
    update_obj.message.reply_text("Type in the numbers of the users you want to add to the event, "
                                  "separated by spaces. To cancel, type 'OK'. Eg: (1 3 2)")
    return settings.THIRD


# Gets the users that the admin wants to add into the group
def join_event_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    current_group = settings.current_group_id[chat_id]

    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Ok, cancelling job")
        return ConversationHandler.END

    users = get_intended_users(message, current_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return ConversationHandler.END

    # Gets the user_ids
    user_ids = [convert_rank_to_id(current_group, rank) for rank in users]
    event_parent_id = settings.event_joining_tracker_storage[chat_id].event_parent_id

    argument_tuple = [(user_id, current_group, event_parent_id) for user_id in user_ids]

    # Now, we insert each of the users into events_users
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            # Makes the timezone correct first
            cur.execute(
                """
                SET timezone TO 'Asia/Singapore'
                """
            )
            cur.executemany(
                """
                INSERT INTO events_users 
                (user_id, group_id, event_parent_id, TimeJoined)
                VALUES 
                (%s, %s, %s, CURRENT_TIMESTAMP(0))
                """, argument_tuple
            )

    update_admin_movements(chat_id=chat_id, group_id=current_group, function='/joinevent',
                           admin_text=f"Group: {settings.event_joining_tracker_storage[chat_id].event_name}\n"
                                      f"Users: {message}")
    update_obj.message.reply_text("All users added to event")
    return ConversationHandler.END


# Gets current events
def get_event(update_obj: Update, context: CallbackContext):
    """Note that this is settings.FIRST state already. Before this we call join_event, to join group"""
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Ok, exiting now", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    current_group = settings.current_group_id[chat_id]

    # We get the event id to join
    event_parent_id, event_name = get_event_id_from_button(message)
    if not event_parent_id:
        update_obj.message.reply_text("Invalid event, please try again!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    get_group_events_backend(update_obj, context, event_parent_id=event_parent_id, group_id=current_group)
    update_admin_movements(chat_id, group_id=current_group, function='/getevent', admin_text=event_name)
    update_obj.message.reply_text("Data about event retrieved", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# Gets history of all events
def get_event_history(update_obj: Update, context: CallbackContext):

    # Need to be admin to get history of all events
    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

    chat_id = update_obj.message.chat_id
    current_group = settings.current_group_id[chat_id]

    update_obj.message.reply_text("Which event's information do you want to get? (Type OK to cancel)",
                                  reply_markup=all_past_events_keyboards(group_id=current_group, extra_options=['OK']))
    return settings.FIRST


def get_event_history_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("Ok, exiting now", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    event_data = message.split()
    event_code = event_data[-1]
    event_datetime = ' '.join([event_data[-3], event_data[-2]])
    event_code = event_code[1:len(event_code) - 1]
    event_datetime = get_datetime_from_time_string(event_datetime)

    current_group = settings.current_group_id[chat_id]

    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SET timezone TO 'Asia/Singapore'
                """
            )
            cur.execute(
                """
                SELECT DISTINCT parent_id
                  FROM events 
                 WHERE event_code = %s
                   AND DateEnd = %s
                """, (event_code, event_datetime)
            )
            data = cur.fetchall()
            if not data:
                update_obj.message.reply_text("Unable to find the event, sorry!")
                return ConversationHandler.END

            event_parent_id = data[0][0]

    get_group_events_backend(update_obj, context, event_parent_id=event_parent_id, group_id=current_group)
    update_admin_movements(chat_id, group_id=current_group, function='/geteventhistory', admin_text=message)
    update_obj.message.reply_text("Data about event retrieved", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


"""Future implementations: 
/selectallofevent : Shows all of that event (idk)  
/eventhistory: Shows a list of all events in the past.
/eventhistorydetailed : Shows a list of all events in the past. List of buttons comes out, choose one event. 
Will call /getevent on that event 
/alleventhistorydetailed: Shows all events in the past 
"""
