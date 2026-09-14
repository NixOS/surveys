"""Import a LimeSurvey TSV over JSON-RPC and assert on what comes back.

Usage: import_check.py <base-url> <survey.txt> <expected_survey.txt> <2026.txt>
Runs inside the test VM against a fresh LimeSurvey; only the standard
library is available. Exits non-zero, with the reason on stderr, on any
RPC error or failed assertion.
"""

import base64
import csv
import json
import sys
import urllib.request


def rpc(url: str, method: str, *params):
    """One JSON-RPC call to LimeSurvey's RemoteControl 2 API.

    LimeSurvey reports failures two ways: a JSON-RPC ``error`` field, or a
    result that is a one-key ``{"status": "..."}`` dict. Both end the run.
    """
    body = json.dumps({"method": method, "params": list(params), "id": 1}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("error"):
        raise SystemExit(f"{method}: {payload['error']}")
    result = payload["result"]
    if isinstance(result, dict) and "status" in result and len(result) == 1:
        raise SystemExit(f"{method}: {result['status']}")
    return result


def import_tsv(url: str, key: str, tsv_path: str) -> int:
    """Import one TSV file and return the survey id LimeSurvey assigned.

    The file is sent base64-encoded, which is what import_survey expects.
    """
    with open(tsv_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    sid = rpc(url, "import_survey", key, data, "txt")
    assert isinstance(sid, int), f"import_survey returned {sid!r}"
    print("imported survey", sid)
    return sid


def check_fixture(url: str, key: str, tsv_path: str) -> None:
    """Import the two-language golden fixture and assert on what was stored.

    The 2025 file is one group in one language, so it leaves most of the
    converter untested. This one covers the rest: a second group, a
    translated G/Q block, the type, other and mandatory flags per question,
    the max_answers attribute, the language settings, and the end text.
    """
    sid = import_tsv(url, key, tsv_path)

    groups = rpc(url, "list_groups", key, sid)
    assert len(groups) == 2, f"expected 2 groups, got {len(groups)}: {groups}"
    # Group order is the converter's link between a group and its
    # translation, so read every list back in that order.
    position = {int(g["gid"]): int(g["group_order"]) for g in groups}
    de_groups = sorted(
        rpc(url, "list_groups", key, sid, "de"), key=lambda g: position[int(g["gid"])]
    )
    names = [g["group_name"] for g in de_groups]
    assert names == ["Über dich", "Nutzung"], f"German group names: {names}"

    questions = [q for q in rpc(url, "list_questions", key, sid) if str(q["parent_qid"]) == "0"]
    questions.sort(key=lambda q: (position[int(q["gid"])], int(q["question_order"])))
    codes = [q["title"] for q in questions]
    assert codes == ["country", "age", "os", "priorities", "nixVersion", "feedback"], codes
    types = [q["type"] for q in questions]
    assert types == ["L", "!", "M", "R", "S", "T"], types
    other = [q["other"] for q in questions]
    assert other == ["N", "N", "Y", "N", "N", "N"], other
    mandatory = [q["mandatory"] for q in questions]
    assert mandatory == ["N", "Y", "S", "N", "N", "N"], mandatory

    de_questions = {
        q["title"]: q
        for q in rpc(url, "list_questions", key, sid, None, "de")
        if str(q["parent_qid"]) == "0"
    }
    prompt = de_questions["country"]["question"]
    assert prompt == "Wo lebst du?", f"German country prompt: {prompt!r}"

    qid = next(q["qid"] for q in questions if q["title"] == "priorities")
    props = rpc(url, "get_question_properties", key, int(qid), ["attributes"])
    attributes = props["attributes"]
    assert isinstance(attributes, dict), f"attributes came back as {attributes!r}"
    max_answers = attributes.get("max_answers")
    assert max_answers == "2", f"max_answers came back as {max_answers!r} from {attributes!r}"

    languages = rpc(url, "get_survey_properties", key, sid, ["language", "additional_languages"])
    assert languages == {"language": "en", "additional_languages": "de"}, languages

    locale = rpc(url, "get_language_properties", key, sid, ["surveyls_endtext"], "de")
    assert "Danke fürs Mitmachen" in locale["surveyls_endtext"], locale
    print("fixture assertions passed")


def check_2026(url: str, key: str, tsv_path: str) -> None:
    """Import the 2026 survey and assert on what LimeSurvey stored.

    2026 is the first year with more than one group, with max_answers on a
    multiple-choice question, with alphabetical answer order, and with a
    250-option question. None of that is covered by the 2025 file or by the
    golden fixture.
    """
    sid = import_tsv(url, key, tsv_path)

    groups = rpc(url, "list_groups", key, sid)
    assert len(groups) == 8, f"expected 8 groups, got {len(groups)}"
    position = {int(g["gid"]): int(g["group_order"]) for g in groups}
    names = [g["group_name"] for g in sorted(groups, key=lambda g: position[int(g["gid"])])]
    assert names[0] == "About you" and names[-1] == "Finally", names

    questions = [q for q in rpc(url, "list_questions", key, sid) if str(q["parent_qid"]) == "0"]
    assert len(questions) == 40, f"expected 40 questions, got {len(questions)}"
    by_code = {q["title"]: q for q in questions}

    def attributes(qid: int) -> dict:
        """get_question_properties returns the string 'No available attributes'
        rather than an empty dict when a question has none."""
        props = rpc(url, "get_question_properties", key, qid, ["attributes"])["attributes"]
        assert isinstance(props, dict), f"attributes came back as {props!r}"
        return props

    # A 250-option dropdown is the one thing here that could hit an unknown
    # limit, and alphabetical ordering is what makes it usable in five
    # languages. LimeSurvey 6 stores our alphasort as answer_order.
    country = by_code["country"]
    assert country["type"] == "!", country["type"]
    options = rpc(url, "get_question_properties", key, int(country["qid"]), ["answeroptions"])
    assert len(options["answeroptions"]) == 250, len(options["answeroptions"])
    assert attributes(int(country["qid"])).get("answer_order") == "alphabetical"

    # max_answers on a multiple-choice question; the golden fixture only covers
    # it on a ranking.
    improvements = by_code["improvements"]
    assert improvements["type"] == "M", improvements["type"]
    assert attributes(int(improvements["qid"])).get("max_answers") == "3"

    # installMethod and hardwareConfig are multiple, not single. Typing either
    # as single ends its 2025 series and the build stays green, so the check
    # belongs here as well as in test_survey_2026.py.
    assert by_code["installMethod"]["type"] == "M", by_code["installMethod"]["type"]
    assert by_code["hardwareConfig"]["type"] == "M", by_code["hardwareConfig"]["type"]

    # The strings aggregate.sankey_funnel matches literally.
    upgrade = by_code["stableUpgrade"]
    options = rpc(url, "get_question_properties", key, int(upgrade["qid"]), ["answeroptions"])
    stored = {o["answer"] for o in options["answeroptions"].values()}
    for label in (
        "I had severe issues and could not make the upgrade.",
        "I had severe issues but figured it out after some time.",
        "I had moderate issues.",
        "I had minor issues.",
        "I had no issues.",
        "I have not upgraded.",
        "I did not know there was a new stable release.",
    ):
        assert label in stored, label

    props = rpc(
        url,
        "get_survey_properties",
        key,
        sid,
        [
            "anonymized",
            "ipaddr",
            "refurl",
            "datestamp",
            "savetimings",
            "format",
            "template",
            "allowprev",
            "showprogress",
        ],
    )
    assert props == {
        "anonymized": "Y",
        "ipaddr": "N",
        "refurl": "N",
        "datestamp": "N",
        "savetimings": "N",
        "format": "G",
        "template": "fruity_twentythree",
        "allowprev": "Y",
        # Not set by the survey file; LimeSurvey defaults it on. Asserted so
        # that a server-side change to the default is caught here rather than
        # by a respondent.
        "showprogress": "Y",
    }, props

    # Ampersands reach LimeSurvey unescaped. It encodes on render, so escaping
    # in the converter reached the respondent as "Antigua &amp; Barbuda".
    country = by_code["country"]
    options = rpc(url, "get_question_properties", key, int(country["qid"]), ["answeroptions"])
    names = {o["answer"] for o in options["answeroptions"].values()}
    assert "Antigua & Barbuda" in names, [n for n in names if "Antigua" in n]
    assert not any("&amp;" in n for n in names), [n for n in names if "&amp;" in n]

    print("2026 assertions passed")


def main(base_url: str, tsv_path: str, fixture_path: str, tsv_2026: str) -> None:
    """Import all three files, then compare what LimeSurvey stored with what
    the files say: for the 2025 survey the group count, top-level question
    count, each question's code and type letter, and the survey-level privacy
    settings; for the golden fixture the checks in check_fixture; for 2026 the
    checks in check_2026.
    """
    url = f"{base_url}/index.php/admin/remotecontrol"
    key = rpc(url, "get_session_key", "admin", "password")
    try:
        sid = import_tsv(url, key, tsv_path)

        groups = rpc(url, "list_groups", key, sid)
        assert len(groups) == 1, f"expected 1 group, got {len(groups)}"

        # list_questions returns subquestions too (Survey.allQuestions has no
        # parent_qid filter), so keep only the top-level questions.
        questions = [q for q in rpc(url, "list_questions", key, sid) if str(q["parent_qid"]) == "0"]
        assert len(questions) == 47, f"expected 47 questions, got {len(questions)}"
        codes = sorted(q["title"] for q in questions)
        assert len(set(codes)) == 47, "expected 47 distinct question codes"

        # Type letters, read back from our own file.
        with open(tsv_path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t", quotechar='"'))
        expected = {r["name"]: r["type/scale"] for r in rows if r["class"] == "Q"}
        actual = {q["title"]: q["type"] for q in questions}
        assert actual == expected, f"type mismatch: {set(actual.items()) ^ set(expected.items())}"

        props = rpc(
            url,
            "get_survey_properties",
            key,
            sid,
            ["anonymized", "ipaddr", "refurl", "datestamp", "savetimings", "format", "language"],
        )
        assert props == {
            "anonymized": "Y",
            "ipaddr": "N",
            "refurl": "N",
            "datestamp": "N",
            "savetimings": "N",
            "format": "G",
            "language": "en",
        }, props
        print("2025 assertions passed")

        check_fixture(url, key, fixture_path)
        check_2026(url, key, tsv_2026)
        print("all assertions passed")
    finally:
        rpc(url, "release_session_key", key)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
