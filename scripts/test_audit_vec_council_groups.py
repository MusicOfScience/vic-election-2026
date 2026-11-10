"""Synthetic, contact-safe tests for official VEC Council group extraction."""
import unittest

from audit_vec_council_groups import reconcile_region, text_of_page

REGION = "Eastern Victoria"
ROSTER = [
    ["Council", REGION, 1, "GIVEN, Alice", "Part A"],
    ["Council", REGION, 2, "SURNAME, Bob", "Part A"],
    ["Council", REGION, 3, "CHOW, Lily", None],
    ["Council", REGION, 4, "CHOW, Kate", None],
    ["Council", REGION, 5, "SOLO, Jane", None],
]

def fixture(reorder=False, omit_group=False):
    a, b = (ROSTER[1][3], ROSTER[0][3]) if reorder else (ROSTER[0][3], ROSTER[1][3])
    grp = "C. Unnamed-1" if omit_group else "B. Unnamed-1"
    return ("""
        <html><head><title>Candidates for Eastern Victoria Region</title></head>
        <body><h1>Candidates for Eastern Victoria</h1>
        <p>The groups and candidates for this region election are below in the order they'll appear on the ballot paper.</p>
        <section><h3>A. Part A</h3><p>0 group voting tickets registered</p>
        <h3>A. Part A</h3>
        <div>""" + a + """ Part A Somewhere</div>
        <div>""" + b + """ Part A Somewhere</div>
        <h3>""" + grp + """</h3>
        <div>CHOW, Lily Somewhere</div>
        <div>CHOW, Kate Somewhere</div>
        <h3>Ungrouped</h3>
        <div>SOLO, Jane Somewhere</div>
        </section><p>© Victorian Electoral Commission</p></body></html>
    """).encode()


class CouncilGroupTests(unittest.TestCase):
    def test_exact_source_names_group_letters_and_ungrouped(self):
        result = reconcile_region(fixture(), REGION, ROSTER)
        self.assertEqual(result["candidateCount"], 5)
        self.assertEqual(result["letteredGroups"], 2)
        self.assertEqual(result["ungroupedCandidates"], 1)
        self.assertEqual([x["group"] for x in result["candidates"]],
            ["A", "A", "B", "B", "Ungrouped"])
        self.assertEqual([x["withinGroupOrdinal"] for x in result["candidates"]],
            [1, 2, 1, 2, 1])
        self.assertEqual(result["groups"][1]["label"], "unnamed-1")
        self.assertFalse(any("phone" in str(x) or "email" in str(x)
                             for x in result["candidates"]))

    def test_out_of_order_nominee_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Candidate not found"):
            reconcile_region(fixture(reorder=True), REGION, ROSTER)

    def test_missing_letter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Non-contiguous"):
            reconcile_region(fixture(omit_group=True), REGION, ROSTER)

    def test_wrong_election_or_missing_authoritative_header_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Wrong region"):
            reconcile_region(fixture(), "Western Victoria", ROSTER)
        wrong = fixture().replace(b"The groups and candidates for this region election", b"Draft candidate list")
        with self.assertRaisesRegex(ValueError, "No VEC final"):
            text_of_page(wrong, REGION)


if __name__ == "__main__":
    unittest.main()
