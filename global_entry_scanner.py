#!/usr/bin/python

"""
Polls the TTP global entry appointment API for the next available appointments,
and notifies if there is an earlier appointment.

Appointment API endpoint: https://ttp.cbp.dhs.gov/schedulerapi/slots
List of locations: https://ttp.cbp.dhs.gov/schedulerapi/locations/
"""

import datetime
import json
import random
import smtplib
import time
import urllib.request

from email.mime.text import MIMEText

QUERY="https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit={limit}&locationId={location}&minimum=1"
DATE_FORMAT="%Y-%m-%dT%H:%M"

# CONFIGURABLE VARIABLES
QUERY_LIMIT=5
QUERY_LOCATION=5446         # E.g., 5446 for San Francisco
EARLIER_THAN="2021-12-31"

SCAN_INTERVAL_SECS = 60     # Scan interval
NO_REPEAT = True            # If true, notify only once per appointment slot
SKIP_TIMES = [              # Do not notify for these times; must be in DATE_FORMAT
    "2021-12-25T08:00",
    "2021-12-25T09:00",
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "username@email_provider.com"
EMAIL_SENDER_PASSWORD = "password"
RECIP_ADDR = "username@email_provider.com"  # The recipient address
USE_SMS = False                             # If true, include SMS_ADDR in recipients list
SMS_ADDR = "1234567890@txt.att.net"         # To use, change the domain to your carrier's

class Scanner(object):
    """
    Provides scanning methods and stores state.
    """
    def __init__(self):
        self.earlier_than = datetime.datetime.strptime(EARLIER_THAN, "%Y-%m-%d").date()
        self.notified = {}
        for t in SKIP_TIMES:
            self.notified[t] = True

    def _get_slots(self):
        """
        Checks for the next available appointment slot(s) and returns non-null if
        there are slots before EARLIER_THAN.
        
        Returns:
            list of available times on the next (single) day
        """
        resp = urllib.request.urlopen(QUERY.format(limit=QUERY_LIMIT, location=QUERY_LOCATION))
        slots = json.loads(resp.read())
        earliest_date = self.earlier_than
        times = []
        for slot in slots:
            dt = datetime.datetime.strptime(slot["startTimestamp"], DATE_FORMAT)
            if dt.date() > earliest_date:
                continue
            elif dt.date() < earliest_date:
                times = []
                earliest_date = dt.date()
            times.append(dt)

        if times:
            print(f"[INFO] Scraper found {len(times)} earlier times on {earliest_date}; invoking notifier")
        else:
            print(f"[INFO] Scraper found no earlier times")
        return times

    def _notify(self, times):
        """
        Sends an email to RECIP_ADDR and SMS_ADDR (if enabled).
        
        Args:
            times: array of datetime.datetime objects
        """
        # 0. Ignore all already-notified times.
        if NO_REPEAT:
            new_times = []
            old_times = []
            for t in times:
                key = t.strftime(DATE_FORMAT)
                if key in self.notified:
                    old_times.append(t)
                else:
                    new_times.append(t)
        else:
            new_times = times
            old_times = []

        if new_times:
            print(f"[INFO] Notifier found {len(new_times)} new times, {len(old_times)} old times")
        else:
            print(f"[INFO] Notifier found no new times, {len(old_times)} old times; skipping")
            return

        # 1. Build the email message.
        date = new_times[0].strftime("%Y-%m-%d")
        plural = ""
        if len(new_times) > 1:
            plural = "s"

        body = f"New appointment{plural} available on {date}:\n"
        for t in new_times:
            body += "\t{0}\n".format(t.strftime("%H:%M"))

        msg = MIMEText(body)
        msg["From"] = EMAIL_SENDER
        msg["To"] = RECIP_ADDR
        msg["Subject"] = f"[Global Entry Scanner] New Appointment{plural} Available on: {date}"
        
        # 2. Send the email.
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        notify_success = False
        try:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_SENDER_PASSWORD)

            if USE_SMS:
                recipients = [RECIP_ADDR, SMS_ADDR]
            else:
                recipients = [RECIP_ADDR]
            print(f"[INFO] Sending email to {recipients}")
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
            notify_success = True
        except smtplib.SMTPException as e:
            print(f"[ERROR] Failed to send email: {e}")
        finally:
            server.quit()
        
        # 3. If notification was successful, don't notify for the same time(s) again.
        if NO_REPEAT and notify_success:
            for t in new_times:
                key = t.strftime(DATE_FORMAT)
                self.notified[key] = True

    def scan_once(self):
        """
        Scan once for an earlier appointment slot and notify if applicable.
        """
        times = self._get_slots()
        if times:
            self._notify(times)

def main():
    scanner = Scanner()
    while True:
        t = time.time()
        scanner.scan_once()
        elapsed = time.time() - t
        jitter = SCAN_INTERVAL_SECS / 10
        jitter = (random.random() - 0.5) * jitter
        # Add 10% jitter to scan every once [9/10, 11/10] * SCAN_INTERVAL_SECS.
        sleep_secs = SCAN_INTERVAL_SECS - elapsed + jitter
        if sleep_secs > 0:
            time.sleep(sleep_secs)

if __name__ == "__main__":
    main()
