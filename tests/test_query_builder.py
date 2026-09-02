import unittest

from app.query_builder import QueryValidationError, build_select_query
from app.resources import CASES, ENTITY_ATTRIBUTES, EXTRACTED_ENTITY_RELATIONSHIPS


class QueryBuilderTests(unittest.TestCase):
    def test_builds_field_search(self):
        query = build_select_query(
            CASES, {"field": ["caseCategory"], "search": ["fraud"]}
        )

        self.assertIn("CAST(case_category AS TEXT) ILIKE %s", query.statement)
        self.assertEqual(query.parameters, ("%fraud%",))

    def test_builds_keyword_search_across_all_fields(self):
        query = build_select_query(CASES, {"search": ["fraud"]})

        self.assertEqual(query.parameters, ("%fraud%",) * 9)
        self.assertEqual(query.statement.count(" ILIKE %s"), 9)

    def test_combines_direct_filters_with_and(self):
        query = build_select_query(
            CASES, {"id": ["1001"], "caseCategory": ["fraud"]}
        )

        self.assertIn("id = %s", query.statement)
        self.assertIn("CAST(case_category AS TEXT) ILIKE %s", query.statement)
        self.assertEqual(query.parameters, (1001, "%fraud%"))

    def test_rejects_non_integer_exact_filter(self):
        with self.assertRaisesRegex(QueryValidationError, "id must be an integer"):
            build_select_query(CASES, {"id": ["not-a-number"]})

    def test_escapes_keyword_wildcards(self):
        query = build_select_query(CASES, {"search": ["100%_complete"]})

        self.assertEqual(query.parameters[0], "%100\\%\\_complete%")

    def test_entity_foreign_key_filter_uses_integer_equality(self):
        query = build_select_query(ENTITY_ATTRIBUTES, {"entityId": ["1028"]})

        self.assertIn("entity_id = %s", query.statement)
        self.assertEqual(query.parameters, (1028,))

    def test_extracted_resource_selects_jsonb_with_camel_case_alias(self):
        query = build_select_query(
            EXTRACTED_ENTITY_RELATIONSHIPS, {"caseId": ["7001"]}
        )

        self.assertIn('extracted_details AS "extractedDetails"', query.statement)
        self.assertIn("case_id = %s", query.statement)
        self.assertEqual(query.parameters, (7001,))
