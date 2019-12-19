#!/usr/bin/env python3

import re
import time
import json
from datetime import tzinfo, timedelta, datetime, time as dtime
import pypyodbc as pyodbc
# import pyodbc
# import webcolors

db = None
def dbConn(db_host = 'localhost', db_name = 'domjudge', db_user = 'domjudge', db_password = ''):
    connection_string = 'Driver={MySQL ODBC 8.0 Unicode Driver};Server=' + db_host + ';Database=' + db_name + ';UID=' + db_user + ';PWD=' + db_password + ';'
    return pyodbc.connect(connection_string)

cid = 0
st = 0
class UTC(tzinfo):
    def __init__(self,offset = 0):
        self._offset = offset
    def utcoffset(self, dt):
        return timedelta(hours=self._offset)
    def tzname(self, dt):
        return "UTC +%s" % self._offset
    def dst(self, dt):
        return timedelta(hours=self._offset)

def dbGetAll(sheet, nc = False, id = 'id'):
    dic = {}
    cursor = db.cursor()
    where = "" if nc else " WHERE cid = %d" % cid
    cursor.execute("SELECT * FROM " + sheet + where)
    row = cursor.fetchone()
    while row:
        dic[row[id]] = {}
        for i in row.field_dict: dic[row[id]][i] = row[i]
        row = cursor.fetchone()
    cursor.close()
    return dic

def select_contest():
    global cid
    contests = dbGetAll("contest", True, 'cid')
    if len(contests) == 0:
        # raise("No contest found")
        print("No contest found")
        return -1
    if len(contests) == 1:
        for i in contests:
            cid = i
            return contests[i]
    now = time.time()
    print("#\tshortname\tactive\tfinalize\tpublic\tname")
    for i in contests:
        print("%d\t%s\t%s\t%s\t%s\t%s" % (
            i,
            contests[i]["shortname"],
            "Active" if contests[i]["activatetime"] <= now and contests[i]["deactivatetime"] > now and contests[i]["enabled"] else "Deactive",
            "True" if contests[i]["finalizetime"] else "False",
            "True" if contests[i]["public"] else "False",
            contests[i]["name"]
        ))
    cid = int(input("Input the contest id you want to gen feed-event: "))
    if not cid in contests:
        print("Contest not found")
        return -1
    return contests[cid]

def stamp2str(t):
    return datetime.fromtimestamp(t, tz=UTC(8)).isoformat()
def timedura(a, b):
    # return dtime(a - b).isoformat()
    return datetime.fromtimestamp(a - b, tz=UTC(0)).time().isoformat()
# contest
# # state
def gen_contest(info):
    global st
    st = info["starttime"]
    contest = {
        "formal_name": info["name"],
        "penalty_time": 20,
        "start_time": stamp2str(info["starttime"]),
        "end_time":   stamp2str(info["endtime"]),
        "duration":                   timedura(info["endtime"], info["starttime"]),
        "scoreboard_freeze_duration": timedura(info["endtime"], info["freezetime"]),
        "id": cid,
        "external_id": info["externalid"],
        "name": info["name"],
        "shortname": info["shortname"]
    }
    state = {
        "started":        None if not info["starttime"]    else stamp2str(info["starttime"]),
        "ended":          None if not info["endtime"]      else stamp2str(info["endtime"]),
        "frozen":         None if not info["freezetime"]   else stamp2str(info["freezetime"]),
        "thawed":         None if not info["unfreezetime"] else stamp2str(info["unfreezetime"]),
        "finalized":      None if not info["finalizetime"] else stamp2str(info["finalizetime"]),
        "end_of_updates": None
    }
    return { "contest": contest, "state": state }

# judgement-types
def gen_judgement_type():
    dic = {
        "AC":  {"id": "AC",  "name": "correct",            "penalty": False, "solved": True},
        "CE":  {"id": "CE",  "name": "compiler error",     "penalty": False, "solved": False},
        "MLE": {"id": "MLE", "name": "memory limit",       "penalty": True,  "solved": False},
        "NO":  {"id": "NO",  "name": "no output",          "penalty": True,  "solved": False},
        "OLE": {"id": "OLE", "name": "output limit",       "penalty": True,  "solved": False},
        "PE":  {"id": "PE",  "name": "presentation error", "penalty": True,  "solved": False},
        "RTE": {"id": "RTE", "name": "run error",          "penalty": True,  "solved": False},
        "TLE": {"id": "TLE", "name": "timelimit",          "penalty": True,  "solved": False},
        "WA":  {"id": "WA",  "name": "wrong answer",       "penalty": True,  "solved": False}
    }
    return dic
# # language
def gen_language():
    dic = {
        "c":  {"id": "c", "name": "C", "extensions": ["c"], "filter_compiler_files": True, "allow_judge": True, "time_factor": 1.0, "require_entry_point": False, "entry_point_description": None},
        "cpp":  {"id": "cpp", "name": "C++", "extensions": ["cpp", "cc", "cxx", "c++"], "filter_compiler_files": True, "allow_judge": True, "time_factor": 1.0, "require_entry_point": False, "entry_point_description": None},
        "java": {"id": "java", "name": "Java", "extensions": ["java"], "filter_compiler_files": True, "allow_judge": True, "time_factor": 2.0, "require_entry_point": False, "entry_point_description": "Main class"},
        "python3":  {"id": "python3", "name": "Python 3", "extensions": ["py3", "py"], "filter_compiler_files": True, "allow_judge": True, "time_factor": 1.0, "require_entry_point": False, "entry_point_description": "Main file"}
    }
    return dic

# testcase
def testcase_count(probid):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) AS c FROM testcase WHERE probid = %d" % probid)
    row = cursor.fetchone()
    count = row["c"]
    cursor.close()
    return count

# problem
# contestproblem
def gen_problem():
    dic = {}
    contestproblems = dbGetAll("contestproblem", id='probid')
    problems = dbGetAll("problem", True, 'probid')
    c = 0
    for i in contestproblems:
        item = {
            "ordinal": c,
            "id": i,
            "short_name": contestproblems[i]["shortname"],
            "label": contestproblems[i]["shortname"],
            "time_limit": problems[i]["timelimit"],
            "externalid": problems[i]["externalid"],
            "name": problems[i]["name"],
            "rgb": contestproblems[i]["color"], # name_to_hex(contestproblems[i]["color"])
            "color": contestproblems[i]["color"],
            "test_data_count": testcase_count(i)
        }
        c += 1
        dic[i] = item
    return dic

# groups
# # team_category
def gen_group():
    dic = {}
    categorys = dbGetAll("team_category", True, 'categoryid')
    for i in categorys:
        item = {
            "hidden": not bool(categorys[i]["visible"]),
            "icpc_id": categorys[i]["categoryid"], # Same as id
            "id": i,
            "name": categorys[i]["name"],
            "sortorder": categorys[i]["sortorder"],
            "color": categorys[i]["color"]
        }
        dic[i] = item
    return dic

# organizations
# # team_affiliation
def gen_organizations():
    dic = {}
    affiliations = dbGetAll("team_affiliation", True, 'affilid')
    for i in affiliations:
        item = {
            "icpc_id": affiliations[i]["externalid"],
            "shortname": affiliations[i]["shortname"],
            "id": i,
            "name": affiliations[i]["shortname"],
            "formal_name": affiliations[i]["name"],
            "country": affiliations[i]["country"]
        }
        dic[i] = item
    return dic

# team
def gen_team(affiliations):
    dic = {}
    teams = dbGetAll("team", True, 'teamid')
    # affiliations = dbGetAll("team_affiliation", True, 'affilid')
    for i in teams:
        affil = None if not teams[i]["affilid"] else affiliations[teams[i]["affilid"]]
        item = {
            "externalid": teams[i]["externalid"],
            "group_ids": [ teams[i]["categoryid"] ],
            "affiliation": None if not affil else affil["formal_name"],
            "id": i,
            "icpc_id": teams[i]["teamid"], # Same as id
            "name": teams[i]["name"],
            "organization_id": teams[i]["affilid"],
            "members": teams[i]["members"]
        }
        dic[i] = item
    return dic

# submission
def gen_submission():
    dic = {}
    submissions = dbGetAll("submission", id='submitid')
    for i in submissions:
        item = {
            "language_id": submissions[i]["langid"],
            "time": stamp2str(submissions[i]["submittime"]),
            "contest_time": timedura(submissions[i]["submittime"], st),
            "id": i,
            "externalid": submissions[i]["externalid"],
            "team_id": submissions[i]["teamid"],
            "problem_id": submissions[i]["probid"],
            "entry_point": submissions[i]["entry_point"],
            "files":[{
                "href": "contests/%d/submissions/%d/files" % (cid, i),
                "mime": "application/zip"
            }]
        }
        dic[i] = item
    return dic

# # judging_run
# def gen_runs(cid):
# # # judging_run_output

# judging / judgements
def gen_judging(judgement):
    dic = {}
    judgings = dbGetAll("judging", id='judgingid')
    for i in judgings:
        if not judgings[i]["valid"]: continue
        item = {
            "max_run_time": float(0),
            "start_time": stamp2str(judgings[i]["starttime"]),
            "start_contest_time": timedura(judgings[i]["starttime"], st),
            "end_time": stamp2str(judgings[i]["endtime"]),
            "end_contest_time": timedura(judgings[i]["endtime"], st),
            "id": i,
            "submission_id": judgings[i]["submitid"],
            "valid": bool(judgings[i]["valid"]),
            "judgehost": judgings[i]["judgehost"],
            "judgement_type_id": judgement[judgings[i]["result"]]
        }
        dic[i] = item
    return dic

# # clarifications

static_event_id = 1
def genEvent(typ, data, id=0, op="create", time=None):
    global static_event_id
    e = {
        "id": id if id else static_event_id,
        "type": typ,
        "op": op,
        "data": data,
        "time": time if time else datetime.now(UTC(8)).isoformat()
    }
    static_event_id += 1
    return json.dumps(e) + "\n"

def main():
    global db
    db = dbConn(db_user="root")
    contest = select_contest()
    if contest == -1: return
    info = gen_contest(contest)
    judgement_types = gen_judgement_type()
    problem = gen_problem()
    groups = gen_group()
    organizations = gen_organizations()
    teams = gen_team(organizations)
    submissions = gen_submission()
    judgement = {}
    for i in judgement_types: judgement[judgement_types[i]["name"].replace(' ', '-')] = i
    judgements = gen_judging(judgement)
    db.close()

    with open("event-feed.json", 'w') as f:
        f.writelines(genEvent("contests", info["contest"]))
        for i in judgement_types:   f.write(genEvent("judgement-types",judgement_types[i]))
        for i in problem:           f.write(genEvent("problems",       problem[i]))
        for i in groups:            f.write(genEvent("groups",         groups[i]))
        for i in organizations:     f.write(genEvent("organizations",  organizations[i]))
        for i in teams:             f.write(genEvent("teams",          teams[i]))
        # f.writelines(genEvent("state", info["state"], op="create"))
        for i in submissions:       f.write(genEvent("submissions",    submissions[i]))
        for i in judgements:        f.write(genEvent("judgements",     judgements[i], op="create"))
        # for i in judgements:        f.write(genEvent("judgements",     judgements[i], op="update"))
        f.writelines(genEvent("state", info["state"], op="update"))

    with open("event.json", 'w') as f:
        data = {
            "contest": {
                "info": info["contest"],
                "state": info["state"],
                "problem":      list(problem.values()),
                "groups":       list(groups.values()),
                "organizations":list(organizations.values()),
                "teams":        list(teams.values()),
                "submissions":  list(submissions.values()),
                "judgements":   list(judgements.values()),
            }
        }
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))

if __name__ == "__main__":
    main()
