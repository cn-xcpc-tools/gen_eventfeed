#!/bin/python3
# coding=utf-8
import os
import re
import json
import time
import datetime

def createOrUpdate(typ, op, data, dit):
    if not typ in dit: dit[typ] = {} # []
    id = data["id"]
    if op == "create":
        dit[typ][id] = data
        # dit[typ].append(data)
    elif op == "update":
        dit[typ][id] = data
        # for i in dit[typ]:
        #     if i["id"] == id:
        #         for l in data: i[l] = data[l]
        #         break
        # if k["id"] != id: print("problem Id not found: " + id)
    elif op == "delete":
        if id in dit[typ]:
            dit[typ][id]["isDelete"] = True
        else:
            dit[typ][id] = { "isDelete": True }
    else: print("Unsupport action: " + op + " on " + typ)
    return dit

def subtime(a, b):
    s = datetime.datetime.fromisoformat(a)
    t = datetime.datetime.fromisoformat(b)
    return (t-s).total_seconds() / 60

def timeoffset(t):
    arr = t.split(':')
    h = int(arr[0])
    m = int(arr[1])
    s = float(arr[2])
    mi = 1 if h >= 0 else -1
    return mi * (abs(h) * 3600 + m * 60 + s)

event = {}
with open('event-feed.json', encoding='utf8') as f:
    for i in f:
        j = json.loads(i)
        if j['type'] == "contests": event["contest"] = j["data"]
        elif j['type'] == "state": event["state"] = j["data"]
        # elif j['type'] == "judgement-types": continue
        elif j['type'] == "organizations": createOrUpdate(j['type'], j['op'], j['data'], event)
        elif j['type'] == "submissions": createOrUpdate(j['type'], j['op'], j['data'], event)
        elif j['type'] == "judgements": createOrUpdate(j['type'], j['op'], j['data'], event)
        # elif j['type'] == "languages": continue
        elif j['type'] == "problems": createOrUpdate(j['type'], j['op'], j['data'], event)
        elif j['type'] == "groups": createOrUpdate(j['type'], j['op'], j['data'], event)
        elif j['type'] == "teams": createOrUpdate(j['type'], j['op'], j['data'], event)
        # elif j['type'] == "runs": continue

# with open('event.json', 'w', encoding='utf8') as f:
#     json.dump(event, f, ensure_ascii=False, indent=2, separators=(',', ': '))

sch = {
    "contest": {
        "info": event["contest"],
        "problem": [],
        "team": [],
        "run": []
    }
}
#problem
for i in event["problems"]:
    j = {
        "id": event["problems"][i]["id"],
        "rgb": event["problems"][i]["rgb"],
        "name": event["problems"][i]["name"],
        "label": event["problems"][i]["label"]
    }
    sch["contest"]["problem"].append(j)

# teams
for i in event["teams"]:
    if not event["teams"][i]["organization_id"]: continue
    a = event["organizations"][event["teams"][i]["organization_id"]]
    j = {
        "id": event["teams"][i]["id"],
        "name": event["teams"][i]["name"],
        # "nationality": a,
        "university": event["teams"][i]["affiliation"], # a["name"]
        "mark": []
    }
    # for k in event["teams"][i]["group_ids"]:
    #     j["mark"].append(event["groups"][k]["name"])
    k = event["teams"][i]["group_ids"][0]
    j["mark"] = event["groups"][k]["name"]

    sch["contest"]["team"].append(j)

# judgements
# for i in event["judgements"]:
#     if not event["judgements"][i]["submission_id"] in event["submissions"]:
#         print("Submission not found: " + event["judgements"][i]["submission_id"])
#         continue
#     s = event["submissions"][event["judgements"][i]["submission_id"]]
#     j = {
#         "team": s["team_id"],
#         "problem": s["problem_id"],
#         "time": timeoffset(s["contest_time"]),
#         "result": event["judgements"][i]["judgement_type_id"]
#     }
#     sch["contest"]["run"].append(j)
for i in event["submissions"]:
    judgement = None
    for k in event["judgements"]:
        if event["judgements"][k]["submission_id"] == i: judgement = event["judgements"][k]
    if not judgement:
        print("Submission not judged: " + i)
        continue
    s = event["submissions"][i]
    if not s["team_id"] in event["teams"]:
        print("Team Deleted: Submission " + i)
        continue
    j = {
        "team": s["team_id"],
        "problem": s["problem_id"],
        "time": timeoffset(s["contest_time"]),
        "result": judgement["judgement_type_id"],
        "status": "done"
    }
    if j["time"] < 0:
        print("Submit befor contest, abort: " + i)
        continue
    sch["contest"]["run"].append(j)

# info
sch["contest"]["info"]["title"] = sch["contest"]["info"]["formal_name"]
sch["contest"]["info"]["short-title"] = sch["contest"]["info"]["shortname"]
sch["contest"]["info"]["length"] = sch["contest"]["info"]["duration"]
sch["contest"]["info"]["scoreboard-freeze-length"] = sch["contest"]["info"]["scoreboard_freeze_duration"]
sch["contest"]["info"]["starttime"] = sch["contest"]["info"]["start_time"]

with open('feed.json', 'w', encoding='utf8') as f:
    json.dump(sch, f, ensure_ascii=False, indent=2, separators=(',', ': '))
