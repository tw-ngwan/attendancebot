from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from backend_implementations import get_admin_reply, get_intended_users, convert_rank_to_id, \
    get_intended_user_swap_pairs, swap_users, get_group_id_from_button, get_group_size, check_admin_privileges, \
    reply_non_admin
from keyboards import group_name_keyboards
import settings
import psycopg2
from data import DATABASE_URL


# Stores added user from add_users
# Because it returns FIRST, it recursively calls itself (hopefully)
def add_user_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, name = get_admin_reply(update_obj, context)
    name = name.strip()
    current_group = settings.current_group_id[chat_id]
    # If user types ok, that means that all users are added
    if name.upper() == "OK":
        update_obj.message.reply_text("Ok, quitting now")
        return ConversationHandler.END

    # Adds the user into the group otherwise
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            # Find current number of users, so that the group rank can be increased
            group_size = get_group_size(current_group)

            # Adds user
            cur.execute(
                """INSERT INTO users
                (group_id, Name, DateAdded, rank)
                VALUES (%s, %s, CURRENT_DATE, %s)
                """, (current_group, name, group_size + 1)
            )

            con.commit()

    update_obj.message.reply_text(f"Ok, {name} added")
    return settings.FIRST


# Verifies that admin really wants to remove users
def remove_user_verification(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)

    # Verify that user really wants to proceed with action
    if message.strip().lower() != "yes":
        update_obj.message.reply_text("Ok, cancelling job now. ")
        return ConversationHandler.END

    update_obj.message.reply_text("Type in the numbers of the users you want to remove, separated by spaces. "
                                  "Note that this action cannot be erased! To cancel, type 'OK'. "
                                  "Eg: (1 3 2)")

    return settings.SECOND


# Removes the users
# First, check that the indices are ok. Then use sqlite to remove the users from the list
def remove_user_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, user_text = get_admin_reply(update_obj, context)
    current_group = settings.current_group_id[chat_id]

    if user_text.strip().upper() == 'OK':
        update_obj.message.reply_text("Ok, cancelling job")
        return ConversationHandler.END

    # Get the users first
    users = get_intended_users(user_text, current_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return ConversationHandler.END

    user_ids = [(convert_rank_to_id(current_group, rank), ) for rank in users]

    # Now, we remove the users from all tables concerned (attendance, users)
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.executemany(
                """
                DELETE FROM attendance
                WHERE user_id = %s""",
                user_ids
            )
            cur.executemany(
                """
                DELETE FROM users
                WHERE id = %s""",
                user_ids
            )

            # In a REALLY bad move, this code is copied/duplicated from change_user_group
            current_group_size = get_group_size(current_group)

            # Now, updates the users table to change the ranks of the original users
            initial_user_parameters = [(i, current_group, i, current_group) for i in
                                       range(current_group_size, 0, -1)]
            cur.executemany(
                # Try and see if this can be cut down
                """
                UPDATE users
                   SET rank = %s 
                 WHERE id = (SELECT id 
                               FROM users 
                              WHERE group_id = %s 
                                AND rank = (SELECT MIN(rank)
                                               FROM users
                                              WHERE rank >= %s
                                                AND group_id = %s
                                )
                )
                """, initial_user_parameters
            )

            # Save changes
            con.commit()

    update_obj.message.reply_text("All users removed")
    return ConversationHandler.END


# Gets the details of the user you want to edit, verifies them
def edit_user_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)

    # Check if need to cancel
    if message == 'OK':
        update_obj.message.reply_text("Ok, cancelling job")
        return ConversationHandler.END

    current_group = settings.current_group_id[chat_id]
    user_parameters = [[val.strip() for val in param.split(':')] for param in message.split('\n')]

    # Check that for each new line, there are two entries separated by a :
    if not min([len(param) == 2 for param in user_parameters]):
        update_obj.message.reply_text("Message entered incorrectly!")
        return ConversationHandler.END

    users, names = zip(*user_parameters)

    # Get the users first
    users = get_intended_users(' '.join(users), current_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return ConversationHandler.END

    # Already have the names. So we combine them into a list of tuples where we can executemany
    ids_to_edit = [(names[i], convert_rank_to_id(current_group, users[i])) for i in range(len(users))]

    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            # Update the table now
            cur.executemany(
                """
                UPDATE users
                SET name = %s 
                WHERE id = %s""",
                ids_to_edit
            )

            con.commit()

    update_obj.message.reply_text("All edits done")
    return ConversationHandler.END


# Changes the group ordering
def change_group_ordering_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    group_id = settings.current_group_id[chat_id]
    pairs_to_swap = get_intended_user_swap_pairs(message, group_id=group_id)
    print(pairs_to_swap)
    # Verify that user input is correct
    if not pairs_to_swap:
        update_obj.message.reply_text("Pairs keyed in an incorrect format!")
        return ConversationHandler.END

    # Swaps all pairs of users in sequence
    for (a, b) in pairs_to_swap:
        swap_users(a, b, group_id)

    update_obj.message.reply_text("All orderings swapped")
    return ConversationHandler.END


# Change user group: Gets the group that the users are to be transferred from, and asks for the final group
def change_user_group_get_initial(update_obj: Update, context: CallbackContext) -> int:
    chat_id, group_message = get_admin_reply(update_obj, context)

    # Tests that the group id is valid (or that OK is not entered)
    group_id, group_name = get_group_id_from_button(group_message)
    if not group_id:
        update_obj.message.reply_text("Ok, cancelling job now")
        return ConversationHandler.END

    # Check that the user has the right privileges
    if check_admin_privileges(chat_id, group_id) > 0:
        # print("False verification")
        reply_non_admin(update_obj, context, settings.ADMIN)
        return False

    # Stores the initial group id
    settings.change_user_group_storage[chat_id] = settings.ChangeUserGroups(group_id)

    groups_button_markup = group_name_keyboards(chat_id)
    # Asks the user for the final group that users are to be transferred to
    update_obj.message.reply_text("Which group do you want the users to be transferred to?",
                                  reply_markup=groups_button_markup)
    return settings.SECOND


# Change user group: Gets the final group, and asks for the list of users that are to be transferred
def change_user_group_get_final(update_obj: Update, context: CallbackContext) -> int:
    chat_id, group_message = get_admin_reply(update_obj, context)

    # Tests that the group id is valid (or that OK is not entered)
    group_id, group_name = get_group_id_from_button(group_message)
    if not group_id:
        update_obj.message.reply_text("Ok, cancelling job now")
        return ConversationHandler.END

    # Check that the user has the right privileges
    if check_admin_privileges(chat_id, group_id) > 0:
        # print("False verification")
        reply_non_admin(update_obj, context, settings.ADMIN)
        return False

    # Stores the final group id, and checks that it is not the same as the initial group
    if group_id == settings.change_user_group_storage[chat_id].initial_group:
        update_obj.message.reply_text("Initial and final group cannot be the same!")
        return ConversationHandler.END
    settings.change_user_group_storage[chat_id].final_group = group_id

    # Asks the user to key in the list of users that he wants transferred from the initial group
    update_obj.message.reply_text("Type in the numbers of the users you want to move from the initial group, "
                                  "separated by spaces. To cancel, type 'OK'. Eg: (1 3 2)")

    return settings.THIRD


# Change user group: Changes the group that the users are in
def change_user_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)

    initial_group = settings.change_user_group_storage[chat_id].initial_group
    final_group = settings.change_user_group_storage[chat_id].final_group

    # Check that the user wants to proceed with the job first
    if message.strip().lower() == 'yes':
        update_obj.message.reply_text("Ok, cancelling job now")
        return ConversationHandler.END

    # Check that the user input is valid, and get the list of users that he wants
    # Keeps the order in which users were inputted
    users = get_intended_users(message, initial_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return ConversationHandler.END

    # Preserve order
    users.sort()

    # Gets the ids of all users
    user_ids = [convert_rank_to_id(initial_group, rank) for rank in users]

    # First, we get the group_size of the final group, so that we can assign the rank
    # Next, we add all users from the initial group to the final group
    # Finally, we change the ranks of the initial group to make it correct once again
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:

            # Get the group sizes
            final_group_size = get_group_size(final_group)
            initial_group_size = get_group_size(initial_group)

            # The list that is passed to the executemany to update the groups of the users
            user_parameters = [(final_group, i + final_group_size + 1, user_ids[i]) for i in range(len(user_ids))]
            print(user_parameters)

            # Updates the users table to change the groups of the users
            cur.executemany(
                """
                UPDATE users
                   SET group_id = %s, rank = %s
                 WHERE id = %s 
                """, user_parameters
            )

            attendance_user_parameters = [(final_group, user_ids[i]) for i in range(len(user_ids))]
            # Updates the attendance table to change the groups of the users
            cur.executemany(
                """
                UPDATE attendance 
                   SET group_id = %s 
                 WHERE user_id = %s
                """, attendance_user_parameters
            )

            # Now, updates the users table to change the ranks of the original users
            initial_user_parameters = [(i, initial_group, i, initial_group) for i in range(initial_group_size, 0, -1)]
            cur.executemany(
                # Try and see if this can be cut down
                """
                UPDATE users
                   SET rank = %s 
                 WHERE id = (SELECT id 
                               FROM users 
                              WHERE group_id = %s 
                                AND rank = (SELECT MIN(rank)
                                               FROM users
                                              WHERE rank >= %s
                                                AND group_id = %s
                                )
                )
                """, initial_user_parameters
                # # Oops this thing doesn't work because it updates all ranks at once
                # # I need something that updates each inidividual rank one by one...
                # # This still does not work. Check how you can do individual
            )

            # Save changes
            con.commit()

    update_obj.message.reply_text("All users shifted")
    return ConversationHandler.END
