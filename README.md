# attendancebot
A bot to keep track of the attendance of an organization.

This attendance bot tracks attendance of groups, of which each group contains members. Each group can be the subgroup of other groups, and the parent of other groups, so this implementation allows for the nesting necessary for there to be layers of groups on top of each other. Each group can be managed by users, of which there are three priority tiers: Observers, Members, and Admins, of which Admins get the full functionality of the bot, and Observers only basic functions. This is to ensure that the attendance of groups cannot be tampered with unnecessarily.

People using the bot can either create a group, or join the necessary group that has already been created (using a group code and password). To call a function on a group, they must use /enter to enter the group first. Users in any group will get a message at various times of the day pinging them about the day's attendance. 

Edit as of 28 Oct 2022: The bot can now be used to keep track of events, through our event tracking mechanism

Technical implementation of the bot:
Data is stored in SQLite in 4 tables: Groups, Users, Attendance, and Admins. Groups stores the groups that are created, Users stores all the names of all the people in each group, Attendance stores the daily attendance of each user, and Admins stores the chat_ids and data of all the people who use the bot (regardless of their tier). Whenever users call a function to change the attendance or get the attendance, the relevant attendance status is stored in the Attendance Table of SQLite, so that it can be called back when needed. Similarly, whenever groups / users are added or deleted, the relevant tables are called. When the attendance of a group is called, it will call recursively for the attendance of all subgroups as well. However, if you want to change the attendance of a subgroup of a group, you need to enter that group first.

There are functions for editing, merging groups, and transferring users between groups if those are needed.

Reading the code:
For an understanding of how telegram's api works, see dummy.py 
To analyse the code, start from main.py, before opening the helper files referenced.

Functions in main.py are split into group functions (regarding groups, such as creating or joining groups), user functions (regarding members, such as adding members), and attendance functions (regarding attendance, such as getting a day's attendance or changing it). For each of the three groups, there are two files, the entry file and the state file (hence 6 files). Basically, the entry file's functions are the ones called by the Telegram api immediately after the user calls the function. Functions in the entry file reference functions in the state file. There is also the entry_help_functions.py file, which implements the starter and help functions, including pinging the user about attendance every day. 

Arguably the most important file is backend_implementations.py, in which all the backend code for the aforementioned files are implemented. Functions here are referenced in the aforementioned files to perform their jobs. keyboards.py provides the backend for the special keyboards used in some functions. settings.py defines some global variables. 

All data is stored in attendance.db
