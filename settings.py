"""File that only contains the state variables"""


def init():
    global current_group
    global FIRST, SECOND, THIRD
    global help_message
    current_group = None
    FIRST, SECOND, THIRD = range(3)
    help_message = """
Here is a walkthrough of what each of the functions will do: 

Start functions: 
/start: Once you activate the bot, it will send you the attendance statuses of each group you're in every day. 
/help: Gives you the list of commands available and explains the concept of "groups" and "subgroups"

Group functions: 
/creategroup: Creates a group within your current group 
/entergroup: Enters group to do stuff in the group
/leavegroup: Leaves group you are currently in, goes one level up. 
/currentgroup: Returns the current group you are in, and None if not 
/deletegroup: Deletes the group. Needs Admin privileges, and prompt to do so
/mergegroups: Merges two groups together, with one becoming the parent group, and the other its child
/joingroupmembers: Joins the members of two groups together, under a new name
/joinexistinggroup: Joins a group that already exists, using its group id. 
/quitexistinggroup: Quits a group you are currently in. 

User functions: 
/addusers: Adds users to the group you are currently in (/entergroup). Recursive, till enter OK
/removeusers: Removes users from the group you are currently in. Recursive, till enter OK 
/editusers: Changes the names and details of the user 
/becomeadmin: Enter a password to become group admin 
/getadmins: Returns a list of all admin users. 
/dismissadmins: Dismisses an admin user. Can only be done with Head Admin Privileges. 

Attendance functions: 
/editsettings: Edits settings. To be elaborated
/changeattendance: Changes the attendance status of any group members of group you are currently in (Admin?)
/changemyattendance: Changes your attendance 
/getgroupattendance: Returns the attendance status of all group members on that day 
/getuserattendance: Returns the attendance status of a user over a period of time (user-defined)
/getallattendance: Returns the attendance status of all group members over a period of time
/backdatechangeattendance: Changes the attendance of a user, backdated. Admin Privileges required. 

/stop: Stops the bot from running. 

To cancel a function you have called, type 'OK'. 

If this is your first time using the bot, call /creategroup to create a new group, or /joingroup to join an existing group. 
If you want to perform a function within a group (eg: /addusers, /getgroupattendance), make sure to call /entergroup first. 
"""
