"""This is an unnecessary file, left for code reference purposes """

import schedule
from threading import Thread
from time import sleep
import psycopg2
from data import DATABASE_URL


# Checks schedule and waits if not time to call function yet
def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


# Updates the attendance for the next day
# What I want this function to do:
# I want the attendance of the whole of next week to be recorded. So on 2pm of day 1,
# I want the attendance of day 8 to be stored in the SQLite table.
# All entries will be P
def update_attendance():

    # First, we find all the groups that need attendance updated
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            # Makes the timezone correct first
            cur.execute(
                """
                SET timezone TO 'Asia/Singapore'
                """
            )
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
                        (%s, %s, %s, CURRENT_DATE + 7, P)""",
                        (group_id, user_id, i + 1)  # 1-indexed
                    )

            con.commit()


# I have no idea how to make this into a function that automatically runs update_attendance
if __name__ == "__main__":
    schedule.every().day.at("00:00").do(update_attendance)

    # Spin up a thread to run the schedule check, so it doesn't block your bot.
    # This will take the function schedule_checker which will check every second
    # to see if the scheduled job needs to be run.
    Thread(target=schedule_checker).start()
