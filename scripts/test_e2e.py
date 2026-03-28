"""End-to-end smoke test for the evaluation API.

Usage:
    python scripts/test_e2e.py

Requires the API to be running on localhost:8000 with a valid OPENAI_API_KEY.
"""

import httpx

BASE = "http://localhost:8000/api/v1"

SAMPLE_PAYLOAD = {
    "candidate_id": "CAND-2026-0042",
    "structured_data": {
        "gpa": 3.87,
        "sat_score": 1480,
        "school_type": "public",
        "school_ranking": "unranked",
        "region": "rural_appalachia",
        "household_income_bracket": "below_30k",
        "first_generation": True,
        "extracurriculars": [
            "Founded coding club with 30 members",
            "Part-time job at local grocery store (20 hrs/week)",
            "Volunteered at community health clinic",
        ],
        "awards": [
            "Regional Science Fair - 1st place",
            "AP Scholar with Distinction",
        ],
    },
    "essays": [
        (
            "Growing up in a town where the nearest bookstore was an hour away, "
            "I learned that resourcefulness is its own form of leadership. When "
            "our school lost funding for the computer lab, I organized a "
            "community fundraiser that raised $4,200 in three weeks. That "
            "experience taught me that leading isn't about having authority — "
            "it's about convincing people that a shared goal is worth their "
            "Saturday mornings. I've carried that lesson into every project "
            "since, from building our school's first robotics team to mentoring "
            "younger students who, like me, didn't have role models in STEM."
        ),
        (
            "My biggest failure was also my greatest teacher. In junior year, "
            "I applied to a prestigious summer research program and was "
            "rejected. Instead of retreating, I emailed the program director "
            "asking for feedback and spent the summer designing my own research "
            "project on water quality in local streams. The results were "
            "published in our county's environmental report. I realized that "
            "learning agility isn't about never failing — it's about how "
            "quickly you pivot failure into fuel."
        ),
    ],
}


def main() -> None:
    with httpx.Client(timeout=120) as client:
        # Step 1: Start evaluation
        print("=== Step 1: POST /evaluate ===")
        resp = client.post(f"{BASE}/evaluate", json=SAMPLE_PAYLOAD)
        resp.raise_for_status()
        data = resp.json()
        thread_id = data["thread_id"]

        print(f"  Status : {data['status']}")
        print(f"  Thread : {thread_id}")
        print(f"  State keys: {list(data['state'].keys())}")

        if "essay_analysis" in data["state"]:
            ea = data["state"]["essay_analysis"]
            print(f"  Essay leadership_score : {ea.get('leadership_score')}")
            print(f"  Essay agility_score    : {ea.get('agility_score')}")

        if "integrity_flags" in data["state"]:
            flags = data["state"]["integrity_flags"]
            print(f"  AI-gen probability     : {flags.get('ai_generated_probability')}")
            print(f"  Flagged                : {flags.get('is_flagged')}")

        # Step 2: Resume with human review
        print("\n=== Step 2: POST /evaluate/{thread_id}/resume ===")
        resume_payload = {
            "human_review": {
                "reviewer": "Dr. Smith",
                "notes": "Essays appear authentic. Strong candidate from underserved area.",
                "override_flags": False,
            }
        }
        resp = client.post(f"{BASE}/evaluate/{thread_id}/resume", json=resume_payload)
        resp.raise_for_status()
        result = resp.json()

        print(f"  Status         : {result['status']}")
        fe = result["final_evaluation"]
        print(f"  Overall Score  : {fe.get('overall_score')}/100")
        print(f"  Recommendation : {fe.get('recommendation')}")
        print(f"  Confidence     : {fe.get('confidence')}")
        print(f"  Explanation    : {fe.get('explanation', '')[:200]}...")

    print("\nAll steps completed successfully.")


if __name__ == "__main__":
    main()
