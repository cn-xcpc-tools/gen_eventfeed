#!/usr/bin/env php
<?php
$con = null;
$cid = 0;
$st = 0;
function dbConn($db_host = 'localhost', $db_name = 'domjudge', $db_user = 'domjudge', $db_password = ''){
    $con = new mysqli($db_host, $db_user, $db_password, $db_name);
    if (!$con) {
        die('Could not connect: ' . mysqli_error());
    }
    return $con;
}

function dbGetAll($sheet, $nc = False, $id = 'id') {
    global $con, $cid;
    $dic = [];
    $where = $nc ? "" : sprintf(" WHERE cid = %d", $cid);
    $cursor = $con->query("SELECT * FROM " . $sheet . $where);
    while($row = $cursor->fetch_assoc()) { //->fetch_array(MYSQLI_ASSOC)
        $dic[$row[$id]] = $row;
    }
    $cursor->close();
    return $dic;
}

function testcase_count($probid) {
    global $con;
    $cursor = $con->query(sprintf("SELECT COUNT(*) AS c FROM testcase WHERE probid = %d", $probid));
    $row = $cursor->fetch_array(MYSQLI_NUM);
    $count = $row[0];
    $cursor->close();
    return $count;
}

function stamp2str($t) {
    return date(DATE_ISO8601, $t);
}

function timedura($a, $b) {
    return gmstrftime('%H:%M:%S', $a - $b);
}

function select_contest() {
    global $cid;
    $contests = dbGetAll("contest", True, 'cid');
    if (count($contests) == 0) {
        error_log("No contest found");
        return -1;
    }
    if (count($contests) == 1) {
        foreach($contests as $i=>$v){
            $cid = $i;
            return $v;
        }
    }
    $now = time();
    if (isset($_GET['cid'])) {
        $cid = (int) $_GET['cid'];
        if (!array_key_exists($cid, $contests)) return -1;
    } else {
        error_log("#\tshortname\tactive\tfinalize\tpublic\tname");
        foreach($contests as $i=>$v){
            error_log(sprintf("%d\t%s\t%s\t%s\t%s\t%s",
                $i,
                $v["shortname"],
                $v["activatetime"] <= $now and $v["deactivatetime"] > $now and $v["enabled"],
                $v["finalizetime"] ? true : false,
                $v["public"] ? true : false,
                $v["name"]
            ));
        }
        sscanf(fgets(STDIN), "%d", $cid);
        if (!array_key_exists($cid, $contests)) return -1;
    }
    return $contests[$cid];
}

function gen_contest($info) {
    global $cid, $st;
    $st = $info["starttime"];
    $contest = [
        "formal_name" => $info["name"],
        "penalty_time" => 20,
        "start_time" => stamp2str($info["starttime"]),
        "end_time" =>   stamp2str($info["endtime"]),
        "duration" =>                   timedura($info["endtime"], $info["starttime"]),
        "scoreboard_freeze_duration" => timedura($info["endtime"], $info["freezetime"]),
        "id" => $cid,
        "external_id" => $info["externalid"],
        "name" => $info["name"],
        "shortname" => $info["shortname"]
    ];
    $state = [
        "started" =>        $info["starttime"]    ? stamp2str($info["starttime"]   ) : null,
        "ended" =>          $info["endtime"]      ? stamp2str($info["endtime"]     ) : null,
        "frozen" =>         $info["freezetime"]   ? stamp2str($info["freezetime"]  ) : null,
        "thawed" =>         $info["unfreezetime"] ? stamp2str($info["unfreezetime"]) : null,
        "finalized" =>      $info["finalizetime"] ? stamp2str($info["finalizetime"]) : null,
        "end_of_updates" => null
    ];
    return [ "contest" => $contest, "state" => $state ];
}

function gen_judgement_type() {
    $dic = [
        "AC"  => ["id" => "AC",  "name" => "correct",            "penalty" => False, "solved" => True ],
        "CE"  => ["id" => "CE",  "name" => "compiler error",     "penalty" => False, "solved" => False],
        "MLE" => ["id" => "MLE", "name" => "memory limit",       "penalty" => True,  "solved" => False],
        "NO"  => ["id" => "NO",  "name" => "no output",          "penalty" => True,  "solved" => False],
        "OLE" => ["id" => "OLE", "name" => "output limit",       "penalty" => True,  "solved" => False],
        "PE"  => ["id" => "PE",  "name" => "presentation error", "penalty" => True,  "solved" => False],
        "RTE" => ["id" => "RTE", "name" => "run error",          "penalty" => True,  "solved" => False],
        "TLE" => ["id" => "TLE", "name" => "timelimit",          "penalty" => True,  "solved" => False],
        "WA"  => ["id" => "WA",  "name" => "wrong answer",       "penalty" => True,  "solved" => False]
    ];
    return $dic;
}

function gen_language() {
    $dic = [
        "c"       => [
            "id"                      => "c",
            "name"                    => "C",
            "extensions"              => ["c"],
            "filter_compiler_files"   => True,
            "allow_judge"             => True,
            "time_factor"             => 1.0,
            "require_entry_point"     => False,
            "entry_point_description" => null
        ],
        "cpp"     => [
            "id"                      => "cpp",
            "name"                    => "C++",
            "extensions"              => ["cpp", "cc", "cxx", "c++"],
            "filter_compiler_files"   => True,
            "allow_judge"             => True,
            "time_factor"             => 1.0,
            "require_entry_point"     => False,
            "entry_point_description" => null
        ],
        "java"    => [
            "id"                      => "java",
            "name"                    => "Java",
            "extensions"              => ["java"],
            "filter_compiler_files"   => True,
            "allow_judge"             => True,
            "time_factor"             => 2.0,
            "require_entry_point"     => False,
            "entry_point_description" => "Main class"
        ],
        "python3" => [
            "id"                      => "python3",
            "name"                    => "Python 3",
            "extensions"              => ["py3", "py"],
            "filter_compiler_files"   => True,
            "allow_judge"             => True,
            "time_factor"             => 1.0,
            "require_entry_point"     => False,
            "entry_point_description" => "Main file"
        ]
    ];
    return $dic;
}

function gen_problem() {
    $dic = [];
    $contestproblems = dbGetAll("contestproblem", False, 'probid');
    $problems = dbGetAll("problem", True, 'probid');
    $c = 0;
    foreach($contestproblems as $i=>$v) {
        $item = [
            "ordinal"         => $c,
            "id"              => $i,
            "short_name"      => $v["shortname"],
            "label"           => $v["shortname"],
            "time_limit"      => $problems[$i]["timelimit"],
            "externalid"      => $problems[$i]["externalid"],
            "name"            => $problems[$i]["name"],
            "rgb"             => $v["color"],
            "color"           => $v["color"],
            "test_data_count" => testcase_count($i)
        ];
        $c += 1;
        $dic[$i] = $item;
    }
    return $dic;
}

function gen_group() {
    $dic = [];
    $categorys = dbGetAll("team_category", True, 'categoryid');
    foreach($categorys as $i=>$v) {
        $item = [
            "hidden"    => !$v["visible"],
            "icpc_id"   => $v["categoryid"], # Same as id
            "id"        => $i,
            "name"      => $v["name"],
            "sortorder" => $v["sortorder"],
            "color"     => $v["color"]
        ];
        $dic[$i] = $item;
    }
    return $dic;
}

function gen_organizations() {
    $dic = [];
    $affiliations = dbGetAll("team_affiliation", True, 'affilid');
    foreach($affiliations as $i=>$v) {
        $item = [
            "icpc_id"     => $v["externalid"],
            "shortname"   => $v["shortname"],
            "id"          => $i,
            "name"        => $v["shortname"],
            "formal_name" => $v["name"],
            "country"     => $v["country"]
        ];
        $dic[$i] = $item;
    }
    return $dic;
}

function gen_team($affiliations) {
    $dic = [];
    $teams = dbGetAll("team", True, 'teamid');
    foreach($teams as $i=>$v) {
        $affil = isset($v["affilid"]) ? $affiliations[$v["affilid"]] : null;
        $item = [
            "externalid"      => $v["externalid"],
            "group_ids"       => [ $v["categoryid"] ],
            "affiliation"     => isset($affil) ? $affil["formal_name"] : null,
            "id"              => $i,
            "icpc_id"         => $v["teamid"], # Same as id
            "name"            => $v["name"],
            "organization_id" => $v["affilid"],
            "members"         => $v["members"]
        ];
        $dic[$i] = $item;
    }
    return $dic;
}

function gen_submission() {
    global $cid, $st;
    $dic = [];
    $submissions = dbGetAll("submission", False, 'submitid');
    foreach($submissions as $i=>$v) {
        $item = [
            "language_id"  => $v["langid"],
            "time"         => stamp2str($v["submittime"]),
            "contest_time" => timedura($v["submittime"], $st),
            "id"           => $i,
            "externalid"   => $v["externalid"],
            "team_id"      => $v["teamid"],
            "problem_id"   => $v["probid"],
            "entry_point"  => $v["entry_point"],
            "files"        => [[
                "href" => sprintf("contests/%d/submissions/%d/files", $cid, $i),
                "mime" => "application/zip"
            ]]
        ];
        $dic[$i] = $item;
    }
    return $dic;
}

# # judging_run
# function gen_runs() {}
# # # judging_run_output

function gen_judging($judgement) {
    global $st;
    $dic = [];
    $judgings = dbGetAll("judging", False, 'judgingid');
    foreach($judgings as $i=>$v) {
        $item = [
            "max_run_time"       => (float) 0,
            "start_time"         => stamp2str($v["starttime"]),
            "start_contest_time" => timedura($v["starttime"], $st),
            "end_time"           => stamp2str($v["endtime"]),
            "end_contest_time"   => timedura($v["endtime"], $st),
            "id"                 => $i,
            "submission_id"      => $v["submitid"],
            "valid"              => (bool) $v["valid"],
            "judgehost"          => $v["judgehost"],
            "judgement_type_id"  => $judgement[$v["result"]] ?? $v["result"]
        ];
        $dic[$i] = $item;
    }
    return $dic;
}
# # clarifications

function genEvent($typ, $data, $id=null, $op="create", $time=null) {
    static $event_id = 1;
    $e = [
        "id"   => $id ?? $event_id,
        "type" => $typ,
        "op"   => $op,
        "data" => $data,
        "time" => $time ?? date(DATE_ISO8601)
    ];
    $event_id += 1;
    return json_encode($e) . "\n";
}

function main() {
    global $con;
    $con = dbConn('localhost', 'domjudge', 'root');
    $contest = select_contest();
    if ($contest == -1) return;
    $info = gen_contest($contest);
    $judgement_types = gen_judgement_type();
    $problem = gen_problem();
    $groups = gen_group();
    $organizations = gen_organizations();
    $teams = gen_team($organizations);
    $submissions = gen_submission();
    $judgement = [];
    foreach ($judgement_types as $i=>$v) {
        $judgement[str_replace(' ', '-', $v["name"])] = $i;
    }
    $judgements = gen_judging($judgement);
    mysqli_close($con);

    echo genEvent("contests", $info["contest"]);
    foreach($judgement_types as $i=>$v) echo genEvent("judgement-types", $v);
    foreach($problem         as $i=>$v) echo genEvent("problem",         $v);
    foreach($groups          as $i=>$v) echo genEvent("groups",          $v);
    foreach($organizations   as $i=>$v) echo genEvent("organizations",   $v);
    foreach($teams           as $i=>$v) echo genEvent("teams",           $v);
    foreach($submissions     as $i=>$v) echo genEvent("submissions",     $v);
    foreach($judgements      as $i=>$v) echo genEvent("judgements",      $v);
    echo genEvent("state", $info["state"]);
    /*
    $f = fopen("event.json", 'w');
    $data = [
        "contest" => [
            "info"          => $info["contest"],
            "state"         => $info["state"],
            "problem"       => array_values($problem),
            "groups"        => array_values($groups),
            "organizations" => array_values($organizations),
            "teams"         => array_values($teams),
            "submissions"   => array_values($submissions),
            "judgements"    => array_values($judgements),
        ]
    ];
    fwrite($f, json_encode($data));
    fclose($f);
    */
}

main();
?>