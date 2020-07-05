import json
import time

userlog_event_types = {"warns": "Warn",
                       "bans": "Ban",
                       "kicks": "Kick",
                       "mutes": "Mute",
                       "notes": "Note",
                       "mail": "Mail"}


def get_blank_userlog():
    return {"warns": [],
            "mutes": [],
            "kicks": [],
            "bans": [],
            "notes": [],
            "mail": [],
            "mail_blocked": False,
            "watch": False,
            "name": "n/a"}


def get_userlog():
    with open("data/userlog.json", "r") as f:
        return json.load(f)


def set_userlog(contents):
    with open("data/userlog.json", "w") as f:
        f.write(contents)


def userlog(uid, issuer, reason, event_type, uname: str = ""):
    userlogs = get_userlog()
    uid = str(uid)
    if uid not in userlogs:
        userlogs[uid] = get_blank_userlog()
    if uname:
        userlogs[uid]["name"] = uname

    log_data = {}
    if event_type == "mail":
        log_data = {"body": reason,
                    "timestamp": int(time.time()),
                    "resolved": False,
                    "replier_id": 0,
                    "replier_name": ""}
    else:
        log_data = {"issuer_id": issuer.id,
                    "issuer_name": f"{issuer}",
                    "reason": reason,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
    if event_type not in userlogs[uid]:
        userlogs[uid][event_type] = []
    userlogs[uid][event_type].append(log_data)
    set_userlog(json.dumps(userlogs))
    return len(userlogs[uid][event_type])


def setwatch(uid, issuer, watch_state, uname: str = ""):
    userlogs = get_userlog()
    uid = str(uid)
    # Can we reduce code repetition here?
    if uid not in userlogs:
        userlogs[uid] = get_blank_userlog()
    if uname:
        userlogs[uid]["name"] = uname

    userlogs[uid]["watch"] = watch_state
    set_userlog(json.dumps(userlogs))
    return
