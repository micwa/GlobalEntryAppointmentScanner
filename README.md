# Global Entry Appointment Scanner

## Purpose

Scan for appointment slots for Global Entry interviews. Global Entry is US government Trusted Traveller Program.

## Requirements

* Python 3
* Email address
    * If using gmail, turn on [less secure apps](https://support.google.com/accounts/answer/6010255). Also visit https://accounts.google.com/DisplayUnlockCaptcha if google prevents login
* (optional) Phone number

## How to run

Configure variables in `global_entry_scanner.py`:
* `EARLIER_THAN`
* `QUERY_LOCATION` (locations [here](https://ttp.cbp.dhs.gov/schedulerapi/locations/))
* `EMAIL_SENDER`
* `EMAIL_SENDER_PASSWORD`
* `RECIP_ADDR` (can be the same as `EMAIL_SENDER`)

Other variables are optional. Then in a terminal, run:

```
$ python global_entry_scanner.py
```
