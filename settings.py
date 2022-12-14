"""File that only contains the state variables"""
from collections import defaultdict
current_group_id = defaultdict(lambda: None)
current_group_name = defaultdict(lambda: None)
attendance_date_edit = {}  # For change_any_day_attendance_get_day in state_attendance_functions
group_to_join = {}  # For join_group_get_group_code in state_group_functions
merge_group_storage = {}  # For merge_group functions in entry_group_functions and state_group_functions
change_user_group_storage = {}  # For change_user_group functions in entry_user_functions and state_user_functions
event_tracker_storage = {}  # For tracking events
event_joining_tracker_storage = {}  # For tracking events that are joined
OBSERVER, MEMBER, ADMIN = "Observer", "Member", "Admin"
FIRST, SECOND, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH, EIGHTH, NINTH, TENTH, ELEVENTH, TWELFTH, THIRTEENTH = range(13)
FOURTEENTH, FIFTEENTH, SIXTEENTH, SEVENTEENTH, EIGHTEENTH, NINETEENTH, TWENTIETH, TWENTYFIRST = range(13, 21)
TWENTYSECOND, TWENTYTHIRD, TWENTYFOURTH, TWENTYFIFTH, TWENTYSIXTH, TWENTYSEVENTH = range(21, 27)


# For storing of users when merging groups
class MergeGroupStorage:

    def __init__(self, parent, superparent):
        self.parent = parent
        self.superparent = superparent
        self.join_all_groups = False
        self.child_groups = set()


# For changing the groups that users are part of
class ChangeUserGroups:

    def __init__(self, initial_group):
        self.initial_group = initial_group
        self.final_group = None
        self.users = []


class Event:

    def __init__(self, event_id=None, event_name=None, event_end=None, event_code=None, event_password=None,
                 event_parent_id=None):
        self.event_id = event_id
        self.event_name = event_name
        self.event_end = event_end
        self.event_code = event_code
        self.event_password = event_password
        self.event_parent_id = event_parent_id


def init():
    global current_group_id, current_group_name
    global FIRST, SECOND, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH, EIGHTH, NINTH, TENTH, ELEVENTH, TWELFTH, THIRTEENTH
    global FOURTEENTH, FIFTEENTH, SIXTEENTH, SEVENTEENTH, EIGHTEENTH, NINETEENTH, TWENTIETH, TWENTYFIRST
    global TWENTYSECOND, TWENTYTHIRD, TWENTYFOURTH, TWENTYFIFTH, TWENTYSIXTH, TWENTYSEVENTH
    global help_message, full_help_message
    global OBSERVER, MEMBER, ADMIN
    global attendance_date_edit
    global group_to_join
    global merge_group_storage
    current_group_id = defaultdict(lambda: None)
    current_group_name = defaultdict(lambda: None)
    FIRST, SECOND, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH, EIGHTH, NINTH, TENTH, ELEVENTH, TWELFTH, THIRTEENTH = range(13)
    FOURTEENTH, FIFTEENTH, SIXTEENTH, SEVENTEENTH, EIGHTEENTH, NINETEENTH, TWENTIETH, TWENTYFIRST = range(13, 21)
    TWENTYSECOND, TWENTYTHIRD, TWENTYFOURTH, TWENTYFIFTH, TWENTYSIXTH, TWENTYSEVENTH = range(21, 27)
    attendance_date_edit = {}
    merge_group_storage = {}
    OBSERVER, MEMBER, ADMIN = "Observer", "Member", "Admin"
    # Basic help message
    help_message = """
Here is a walkthrough of what each of the functions will do, and your level needed to perform the functions: 
/start: Once you activate the bot, it will send you the attendance statuses of each group you're in every day. (None)
/help: Gives you the list of commands available (None)
/helpfull: Gives you the full list of commands available (None)
/tutorial: Gives a tutorial to walk through the bot (None)

/enter: Enters group to do stuff in the group (Observer)
/current: Tells you the current group you are in, and None if not (Observer) 
/joingroup: Joins a group that already exists, using its group id. (None) 

/addusers: Adds users to the group you are currently in. Recursive, till enter OK (Member)
/getusers: Gets the names of all users (Observer)

/change: Changes the attendance status of any group members of group you are currently in, for current day (Member)
/changetmr: Changes the attendance status of any group members of group you are currently in, for next day (Member)
/get: Sends a message with the attendance status of all group members (and subgroup members) for current day (Observer)
/gettmr: Sends a message with the attendance status of all group members (and subgroup members) for next day (Observer)

/joinevent: Joins an event, started either by your group or parent group(s) (Member)

/feedback: Sends feedback to the developers (None) 

To perform a function, call /enter first to enter a group. Your actions will be localized within the group. 
"""
    # Full help message with all functions available
    full_help_message = """
Here is a walkthrough of what each of the functions will do, and your level needed to perform the functions: 
/start: Once you activate the bot, it will send you the attendance statuses of each group you're in every day. (None)
/help: Gives you the list of commands available (None)
/helpfull: Gives you the full list of commands available (None)
/tutorial: Gives a tutorial to walk through the bot (None)

/creategroup: Creates a group within your current group. Don't accidentally make subgroups! (None, Admin) 
/enter: Enters group to do stuff in the group (Observer)
/leave: Leaves group you are currently in after you finish doing stuff (Observer) 
/current: Tells you the current group you are in, and None if not (Observer) 
/deletegroup: Deletes the group. Needs Admin privileges, and prompt to do so (Admin) 
/mergegroups: Merges two groups together, with one becoming the parent group, and the other its child (Admin)  
/joingroup: Joins a group that already exists, using its group id. (None) 
/quitgroup: Quits and exits your group. Do NOT confuse with leave! (Observer) 
/changetitle: Changes group title. Admin privileges required. (Admin) 
/getgroupcodes: Sends messages with the group code, and group passwords relative to your level (any)
/uprank: Promotes user to Admin/Member, with the correct password (Observer/Member)
/setusername: Sets your username (any)
/getgrouphistory: Gets a list of the past 100 functions carried out by users of the group (Admin)

/addusers: Adds users to the group you are currently in. Recursive, till enter OK (Member)
/removeusers: Removes users from the group you are currently in. Recursive, till enter OK (Admin)
/editusers: Changes the names and details of the user (Admin)
/getusers: Gets the names of all users (Observer)
/changeordering: Swaps the ranks of two users (Member) 
/changeusergroup: Transfers users from one group to another (Admin) 

/change: Changes the attendance status of any group members of group you are currently in, for current day (Member)
/changetmr: Changes the attendance status of any group members of group you are currently in, for next day (Member)
/changeany: Changes the attendance status of any group members on any day, including backdating (Admin) 
/get: Sends a message with the attendance status of all group members (and subgroup members) for current day (Observer)
/gettmr: Sends a message with the attendance status of all group members (and subgroup members) for next day (Observer)
/getany: Sends a message with the attendance status of all group members (and subgroup members) for any day (Member)
/getusermonth: Sends a message with the attendance status of a user over the past month (Member)
/getuserany: Sends a message with the attendance status of a user over any period of time (Member)
/getallusersmonth: Sends a message with the attendance status of all users in the group over the past month (Admin)
/getallusersany: Sends a message with the attendance status of all users in the group over any period of time (Admin)

/startevent: Starts an event (Member)
/joinevent: Joins an event, started either by your group or parent group(s) (Member)
/getevent: Gets details of a current event (Member) 
/geteventhistory: Gets details of any past event that has ended (Admin)
/eventhelp: A help message that details how to use Events (None)

/feedback: Sends feedback to the developers (None) 

To perform a function, call /enter first to enter a group. Your actions will be localized within the group. 
"""

