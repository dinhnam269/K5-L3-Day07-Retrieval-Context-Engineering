"""Generate audited reviews.json and run starter/agent_metrics.py for all agent runs.

Also produces context-level manual grades (0/1/2) on the test split for Baseline
and Selected configurations as required by BENCHMARK.md Section 2.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


DEV_BASELINE_REVIEWS = [
    {
        "query_id": "q01",
        "answer_grade": 0,
        "citation_support": [],
        "audit_reason": "False abstention: gold chunk hp-book1-ch1-4_p012_paraC_01 was at rank 2 in TF-IDF, but rank 1 chunk (p013_paraC_02, 537 chars) consumed the 800-char budget so rank 2 was dropped by pack_context even after 2 searches.",
    },
    {
        "query_id": "q02",
        "answer_grade": 0,
        "citation_support": [],
        "audit_reason": "False abstention: gold chunk hp-book1-ch1-4_p014_paraC_00 was at rank 2 in TF-IDF, dropped by budget=800 because rank 1 chunk (p014_paraC_01, 526 chars) filled the context window.",
    },
    {
        "query_id": "q03",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Complete and accurate description of Dumbledore's silver hair/beard, half-moon spectacles, bright blue eyes, and crooked nose broken at least twice; directly supported by hp-book1-ch1-4_p018_paraC_00 (page 18).",
    },
    {
        "query_id": "q04",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly answers 'eleven years' and cites hp-book1-ch1-4_p020_paraC_00 (page 20), which explicitly states 'for eleven years I have been trying to persuade people'.",
    },
    {
        "query_id": "q05",
        "answer_grade": 1,
        "citation_support": [True],
        "audit_reason": "Partially complete (grade 1/2): cites hp-book1-ch1-4_p022_paraC_00 (page 22) which confirms Dumbledore wrote a letter, but TF-IDF missed hp-book1-ch1-4_p024_paraC_00 (page 24) describing tucking the letter inside Harry's blankets on the doorstep.",
    },
    {
        "query_id": "q06",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states both the car-crash lie and the first rule ('Don't ask questions'), directly supported by hp-book1-ch1-4_p028_paraC_00 (page 28).",
    },
    {
        "query_id": "q07",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Yvonne was on vacation in Majorca, supported by hp-book1-ch1-4_p030_paraC_00 (page 30).",
    },
    {
        "query_id": "q08",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Harry dreamed about a flying motorcycle, supported by hp-book1-ch1-4_p032_paraC_00 (page 32).",
    },
    {
        "query_id": "q09",
        "answer_grade": 0,
        "citation_support": [],
        "audit_reason": "False abstention after 3 searches: gold chunk hp-book1-ch1-4_p034_paraC_01 (379 chars) was at rank 2 behind p034_paraC_00 (329 chars); combined formatted length 838 > 800 budget.",
    },
    {
        "query_id": "q10",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly lists all three items (video camera, remote control airplane, knocking down Mrs. Figg on racing bike), supported by hp-book1-ch1-4_p037_paraC_00 (page 37).",
    },
    {
        "query_id": "q11",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly lists a lion, an eagle, a badger, and a snake surrounding the letter H, supported by hp-book1-ch1-4_p040_paraC_00 (page 40).",
    },
    {
        "query_id": "q12",
        "answer_grade": 0,
        "citation_support": [],
        "audit_reason": "False abstention after 2 searches: TF-IDF failed to retrieve gold chunk hp-book1-ch1-4_p044_paraC_00 (page 44, sleeping bag at the foot of the front door) due to lexical mismatch.",
    },
    {
        "query_id": "q13",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly identifies the rifle in Uncle Vernon's hands, supported by hp-book1-ch1-4_p050_paraC_00 (page 50).",
    },
    {
        "query_id": "q14",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states term begins September 1 and owl deadline is July 31, supported by hp-book1-ch1-4_p055_paraC_00 (page 55).",
    },
    {
        "query_id": "q15",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Hagrid defines a Muggle as nonmagic folk, supported by hp-book1-ch1-4_p056_paraC_00 (page 56).",
    },
    {
        "query_id": "u01",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention after 2 searches: wand purchase at Ollivander's is in Chapter 5 (not in Chapters 1-4 corpus). Agent properly refused without guessing.",
    },
    {
        "query_id": "u02",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention: corpus mentions Mr. Dursley directs Grunnings (page 12) but never states his salary.",
    },
]


DEV_SELECTED_REVIEWS = [
    {
        "query_id": "q01",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly identifies Grunnings and drills, directly supported by hp-book1-ch1-4_p012_paraC_01 (page 12).",
    },
    {
        "query_id": "q02",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "With budget=1500, rank-2 gold chunk hp-book1-ch1-4_p014_paraC_00 fits in context; agent accurately answers and cites it.",
    },
    {
        "query_id": "q03",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Complete and accurate description of Dumbledore's physical appearance, supported by hp-book1-ch1-4_p018_paraC_00 (page 18).",
    },
    {
        "query_id": "q04",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly answers eleven years, supported by hp-book1-ch1-4_p020_paraC_00 (page 20).",
    },
    {
        "query_id": "q05",
        "answer_grade": 2,
        "citation_support": [True, True],
        "audit_reason": "Dense retrieval + budget=1500 captures both hp-book1-ch1-4_p022_paraC_00 (wrote a letter) and hp-book1-ch1-4_p024_paraC_00 (tucked it in Harry's blankets on the doorstep); both citations are valid and jointly support the complete answer.",
    },
    {
        "query_id": "q06",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states the car-crash lie and the first rule ('Don't ask questions'), supported by hp-book1-ch1-4_p028_paraC_00 (page 28).",
    },
    {
        "query_id": "q07",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Yvonne was on vacation in Majorca, supported by hp-book1-ch1-4_p030_paraC_00 (page 30).",
    },
    {
        "query_id": "q08",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Harry dreamed about a flying motorcycle, supported by hp-book1-ch1-4_p032_paraC_00 (page 32).",
    },
    {
        "query_id": "q09",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "With budget=1500, gold chunk hp-book1-ch1-4_p034_paraC_01 is included in context; agent accurately answers that the snake was bred in the zoo.",
    },
    {
        "query_id": "q10",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly lists all three items broken/crashed/knocked down by Dudley, supported by hp-book1-ch1-4_p037_paraC_00 (page 37).",
    },
    {
        "query_id": "q11",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly lists lion, eagle, badger, and snake, supported by hp-book1-ch1-4_p040_paraC_00 (page 40).",
    },
    {
        "query_id": "q12",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Dense retrieval ranks hp-book1-ch1-4_p044_paraC_00 at #1; agent accurately answers that Uncle Vernon slept at the foot of the front door in a sleeping bag.",
    },
    {
        "query_id": "q13",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Uncle Vernon was holding a rifle, supported by hp-book1-ch1-4_p050_paraC_00 (page 50).",
    },
    {
        "query_id": "q14",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states September 1 and July 31, supported by hp-book1-ch1-4_p055_paraC_00 (page 55).",
    },
    {
        "query_id": "q15",
        "answer_grade": 2,
        "citation_support": [True],
        "audit_reason": "Correctly states Hagrid defines a Muggle as nonmagic folk, supported by hp-book1-ch1-4_p056_paraC_00 (page 56).",
    },
    {
        "query_id": "u01",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention after 2 searches: wand price at Ollivander's is absent from Chapters 1-4.",
    },
    {
        "query_id": "u02",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention: Mr. Dursley's salary is not mentioned in the corpus.",
    },
]


TEST_BASELINE_REVIEWS = [
    {
        "query_id": "q16",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context and answer both complete (grade 2): hp-book1-ch1-4_p023_paraC_00 (page 23) explicitly states 'Young Sirius Black lent it to me'.",
    },
    {
        "query_id": "q17",
        "answer_grade": 1,
        "citation_support": [True, False],
        "context_grade": 1,
        "audit_reason": "Context grade 1 & Answer grade 1: TF-IDF missed page 29 (hp-book1-ch1-4_p029_paraC_00) where Aunt Petunia explicitly says 'Thirty-nine, sweetums'. Instead it retrieved p028_paraC_03 (which mentions 37 presents + buying 2 more) and p028_paraC_04 ('Two more presents. Is that all right?'). Citation p028_paraC_04 does not support the total of 39.",
    },
    {
        "query_id": "q18",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context and answer both complete (grade 2): hp-book1-ch1-4_p041_paraC_01 (page 41) directly states Dudley won the fight for the keyhole so Harry lay flat on his stomach at the crack under the door.",
    },
    {
        "query_id": "q19",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context and answer both complete (grade 2): hp-book1-ch1-4_p058_paraC_00 (page 58) explicitly states 'on Halloween ten years ago. You was just a year old.'",
    },
    {
        "query_id": "q20",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context and answer both complete (grade 2): hp-book1-ch1-4_p059_paraC_01 (page 59) explicitly states Hagrid 'drew a battered pink umbrella from inside his coat' and pointed it like a sword.",
    },
    {
        "query_id": "u03",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention after 2 searches: Sorting Hat banquet occurs in Chapter 7, outside the Chapters 1-4 corpus.",
    },
    {
        "query_id": "u04",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention: Sirius Black's motorcycle license plate number is never mentioned in the text.",
    },
]


TEST_SELECTED_REVIEWS = [
    {
        "query_id": "q16",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context grade 2 & Answer grade 2: hp-book1-ch1-4_p023_paraC_00 (page 23) directly supports Sirius Black lending Hagrid the flying motorcycle.",
    },
    {
        "query_id": "q17",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context grade 2 & Answer grade 2: Dense retrieval + budget=1500 places hp-book1-ch1-4_p029_paraC_00 (page 29, '\"Thirty-nine, sweetums,\" said Aunt Petunia') in context, and the agent cites it directly.",
    },
    {
        "query_id": "q18",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context grade 2 & Answer grade 2: hp-book1-ch1-4_p041_paraC_01 (page 41) directly supports Dudley winning the fight for the keyhole.",
    },
    {
        "query_id": "q19",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context grade 2 & Answer grade 2: hp-book1-ch1-4_p058_paraC_00 (page 58) directly supports Halloween ten years ago when Harry was one year old.",
    },
    {
        "query_id": "q20",
        "answer_grade": 2,
        "citation_support": [True],
        "context_grade": 2,
        "audit_reason": "Context grade 2 & Answer grade 2: hp-book1-ch1-4_p059_paraC_01 (page 59) directly supports the battered pink umbrella pointed like a sword.",
    },
    {
        "query_id": "u03",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention after 2 searches: Sorting Hat placement is not in Chapters 1-4.",
    },
    {
        "query_id": "u04",
        "abstention_correct": True,
        "citation_support": [],
        "audit_reason": "Correct abstention: motorcycle license plate number is absent from the corpus.",
    },
]


def main() -> None:
    cases_path = ROOT_DIR / "starter/data/converted/cases.json"
    runs = [
        ("dev", "dev-agent-baseline", DEV_BASELINE_REVIEWS),
        ("dev", "dev-agent-selected", DEV_SELECTED_REVIEWS),
        ("test", "test-agent-baseline", TEST_BASELINE_REVIEWS),
        ("test", "test-agent-selected", TEST_SELECTED_REVIEWS),
    ]
    all_summaries = {}
    for split, run_name, reviews in runs:
        run_dir = ROOT_DIR / "starter/results" / run_name
        reviews_path = run_dir / "reviews.json"
        traces_path = run_dir / "traces.json"
        summary_path = run_dir / "summary.json"
        reviews_path.write_text(json.dumps(reviews, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        cmd = [
            sys.executable,
            str(ROOT_DIR / "starter/agent_metrics.py"),
            "--cases", str(cases_path),
            "--traces", str(traces_path),
            "--reviews", str(reviews_path),
            "--split", split,
            "--output", str(summary_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        all_summaries[run_name] = json.loads(summary_path.read_text(encoding="utf-8"))
    print(json.dumps(all_summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
