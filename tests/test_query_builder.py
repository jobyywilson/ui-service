import unittest

from app.query_builder import QueryValidationError, build_select_query
from app.resources import CASES, FILES


class QueryBuilderTests(unittest.TestCase):
    def test_builds_field_search(self):
        query = build_select_query(
            CASES, {"field": ["caseCategory"], "search": ["fraud"]}
        )

        self.assertIn("CAST(case_category AS TEXT) ILIKE %s", query.statement)
        self.assertEqual(query.parameters, ("%fraud%",))

    def test_builds_keyword_search_across_all_fields(self):
        query = build_select_query(FILES, {"search": ["invoice"]})

        self.assertEqual(query.parameters, ("%invoice%",) * 8)
        self.assertEqual(query.statement.count(" ILIKE %s"), 8)

    def test_combines_direct_filters_with_and(self):
        query = build_select_query(
            FILES, {"caseId": ["1001"], "fileName": ["evidence"]}
        )

        self.assertIn("case_id = %s", query.statement)
        self.assertIn("CAST(file_name AS TEXT) ILIKE %s", query.statement)
        self.assertEqual(query.parameters, (1001, "%evidence%"))

    def test_rejects_non_integer_exact_filter(self):
        with self.assertRaisesRegex(QueryValidationError, "caseId must be an integer"):
            build_select_query(FILES, {"caseId": ["not-a-number"]})

    def test_escapes_keyword_wildcards(self):
        query = build_select_query(CASES, {"search": ["100%_complete"]})

        self.assertEqual(query.parameters[0], "%100\\%\\_complete%")
