"""Read-only, case-scoped Neo4j graph queries."""

import base64
import binascii
from datetime import date, datetime, timezone


def json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if hasattr(value, "iso_format"):
        return value.iso_format()
    return value


def encode_cursor(offset):
    return base64.urlsafe_b64encode(str(offset).encode()).decode().rstrip("=")


def decode_cursor(cursor):
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        offset = int(raw.decode())
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        raise ValueError("cursor is invalid") from error
    if offset < 0:
        raise ValueError("cursor is invalid")
    return offset


class GraphRepository:
    def __init__(self, driver, database="neo4j"):
        self.driver, self.database = driver, database

    def run(self, query, **parameters):
        options = {"parameters_": parameters}
        if self.database:
            options["database_"] = self.database
        result = self.driver.execute_query(query, **options)
        return [json_value(row.data()) for row in result.records]

    def nodes(self, case_id, limit, offset=0, filters=None):
        filters = filters or {}
        return self.run("""
            MATCH (entity:CanonicalEntity)
            WHERE entity.id IS NOT NULL
              AND (entity.caseId = $case_id OR $case_id IN coalesce(entity.caseIds, []))
              AND (size($entity_types) = 0 OR entity.type IN $entity_types)
              AND ($community_id IS NULL OR entity.communityId = $community_id)
              AND ($search IS NULL OR toLower(coalesce(entity.displayLabel,
                  entity.label, entity.name, '')) CONTAINS toLower($search))
              AND ($warning_status IS NULL
                   OR ($warning_status = 'warning' AND coalesce(entity.hasWarnings, false))
                   OR ($warning_status = 'contradiction' AND coalesce(entity.hasContradictions, false))
                   OR ($warning_status = 'clear' AND NOT coalesce(entity.hasWarnings, false)
                       AND NOT coalesce(entity.hasContradictions, false)))
              AND ($device_id IS NULL OR EXISTS {
                  MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(dr:EvidenceRecord)
                  WHERE dr.deviceId = $device_id })
              AND ($source_file_id IS NULL OR EXISTS {
                  MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(fr:EvidenceRecord)
                  WHERE fr.fileId = $source_file_id })
            OPTIONAL MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(record:EvidenceRecord)
            WITH entity, collect(DISTINCT record.fileId) AS files,
                 collect(DISTINCT record.deviceId) AS devices
            RETURN entity.id AS id, coalesce(entity.type, 'ENTITY') AS type,
                   coalesce(entity.displayLabel, entity.label, entity.name, entity.id) AS label,
                   entity.confidence AS confidence,
                   entity.firstObservedAt AS firstObservedAt,
                   entity.lastObservedAt AS lastObservedAt,
                   size([x IN files WHERE x IS NOT NULL]) AS sourceCount,
                   size([x IN devices WHERE x IS NOT NULL]) AS deviceCount,
                   entity.communityId AS communityId, entity.bridgeScore AS bridgeScore,
                   coalesce(entity.hasWarnings, false) AS hasWarnings,
                   coalesce(entity.hasContradictions, false) AS hasContradictions,
                   properties(entity) AS properties
            ORDER BY coalesce(entity.bridgeScore, 0) DESC,
                     coalesce(entity.confidence, 0) DESC, entity.id
            SKIP $offset LIMIT $fetch_limit
        """, case_id=case_id, entity_types=filters.get("entity_types", []),
             community_id=filters.get("community_id"), search=filters.get("search"),
             warning_status=filters.get("warning_status"),
             device_id=filters.get("device_id"),
             source_file_id=filters.get("source_file_id"), offset=offset,
             fetch_limit=limit + 1)

    def edges(self, node_ids, minimum, limit, filters=None):
        if not node_ids:
            return []
        filters = filters or {}
        return self.run("""
            MATCH (source:CanonicalEntity)-[rel]->(target:CanonicalEntity)
            WHERE source.id IN $node_ids AND target.id IN $node_ids
              AND rel.id IS NOT NULL AND coalesce(rel.confidence, 1.0) >= $minimum
              AND (size($relationship_types) = 0 OR type(rel) IN $relationship_types)
              AND ($observed_from IS NULL OR
                   toString(coalesce(rel.lastObservedAt, rel.firstObservedAt)) >= $observed_from)
              AND ($observed_to IS NULL OR toString(rel.firstObservedAt) <= $observed_to)
              AND ($warning_status IS NULL
                   OR ($warning_status = 'warning' AND coalesce(rel.hasWarnings, false))
                   OR ($warning_status = 'contradiction' AND coalesce(rel.hasContradictions, false))
                   OR ($warning_status = 'clear' AND NOT coalesce(rel.hasWarnings, false)
                       AND NOT coalesce(rel.hasContradictions, false)))
              AND EXISTS { MATCH (:EvidenceRecord)-[:SUPPORTS]->(p:RelationshipEvidence)
                           WHERE p.relationshipId = rel.id }
            OPTIONAL MATCH (record:EvidenceRecord)-[:SUPPORTS]->(proof:RelationshipEvidence)
            WHERE proof.relationshipId = rel.id
            WITH source, rel, target, count(DISTINCT record) AS evidenceCount,
                 collect(DISTINCT record.fileId) AS files,
                 collect(DISTINCT record.deviceId) AS devices
            RETURN rel.id AS id, type(rel) AS type, source.id AS source,
                   target.id AS target, coalesce(rel.confidence, 1.0) AS confidence,
                   coalesce(rel.assertionType, 'EXPLICIT') AS assertionType,
                   true AS directed, properties(rel) AS attributes,
                   {validFrom: rel.validFrom, validTo: rel.validTo,
                    firstObservedAt: rel.firstObservedAt,
                    lastObservedAt: rel.lastObservedAt,
                    precision: coalesce(rel.temporalPrecision, 'SECOND')} AS temporal,
                   evidenceCount,
                   [x IN files WHERE x IS NOT NULL] AS sourceFiles,
                   [x IN devices WHERE x IS NOT NULL] AS devices,
                   coalesce(rel.hasWarnings, false) AS hasWarnings,
                   coalesce(rel.hasContradictions, false) AS hasContradictions
            ORDER BY rel.id LIMIT $limit
        """, node_ids=node_ids, minimum=minimum,
             relationship_types=filters.get("relationship_types", []),
             observed_from=filters.get("observed_from"),
             observed_to=filters.get("observed_to"),
             warning_status=filters.get("warning_status"), limit=limit)

    def _response(self, case_id, nodes, edges, has_more=False, next_cursor=None):
        communities = {n.get("communityId") for n in nodes if n.get("communityId")}
        return {
            "caseId": case_id,
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "nodes": nodes,
            "edges": edges,
            "pagination": {"nextCursor": next_cursor, "hasMore": has_more},
            "summary": {"nodeCount": len(nodes), "edgeCount": len(edges),
                        "communityCount": len(communities),
                        "bridgeEntityCount": sum(n.get("bridgeScore") is not None for n in nodes)},
        }

    def graph(self, case_id, depth, limit, minimum, filters=None, cursor=None):
        offset = decode_cursor(cursor)
        rows = self.nodes(case_id, limit, offset, filters)
        has_more, nodes = len(rows) > limit, rows[:limit]
        edges = self.edges([str(n["id"]) for n in nodes], minimum,
                           limit * depth * 4, filters)
        next_cursor = encode_cursor(offset + limit) if has_more else None
        return self._response(case_id, nodes, edges, has_more, next_cursor)

    def neighborhood(self, case_id, entity_id, depth, limit, minimum, filters=None,
                     cursor=None):
        if not 1 <= depth <= 5:
            raise ValueError("depth must be between 1 and 5")
        filters = filters or {}
        offset = decode_cursor(cursor)
        nodes = self.run(f"""
            MATCH (start:CanonicalEntity {{id: $entity_id}})
            WHERE start.caseId = $case_id OR $case_id IN coalesce(start.caseIds, [])
            MATCH path=(start)-[*0..{depth}]-(entity:CanonicalEntity)
            WHERE entity.id IS NOT NULL
              AND (entity.caseId = $case_id OR $case_id IN coalesce(entity.caseIds, []))
              AND (size($entity_types) = 0 OR entity.type IN $entity_types)
              AND ($community_id IS NULL OR entity.communityId = $community_id)
              AND ($search IS NULL OR toLower(coalesce(entity.displayLabel,
                  entity.label, entity.name, '')) CONTAINS toLower($search))
              AND ($warning_status IS NULL
                   OR ($warning_status = 'warning' AND coalesce(entity.hasWarnings, false))
                   OR ($warning_status = 'contradiction' AND coalesce(entity.hasContradictions, false))
                   OR ($warning_status = 'clear' AND NOT coalesce(entity.hasWarnings, false)
                       AND NOT coalesce(entity.hasContradictions, false)))
              AND ($device_id IS NULL OR EXISTS {{
                  MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(dr:EvidenceRecord)
                  WHERE dr.deviceId = $device_id }})
              AND ($source_file_id IS NULL OR EXISTS {{
                  MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(fr:EvidenceRecord)
                  WHERE fr.fileId = $source_file_id }})
              AND all(r IN relationships(path) WHERE coalesce(r.confidence, 1.0) >= $minimum)
            OPTIONAL MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(record:EvidenceRecord)
            WITH entity, collect(DISTINCT record.fileId) AS files,
                 collect(DISTINCT record.deviceId) AS devices
            RETURN entity.id AS id, coalesce(entity.type, 'ENTITY') AS type,
                   coalesce(entity.displayLabel, entity.label, entity.name, entity.id) AS label,
                   entity.confidence AS confidence,
                   entity.firstObservedAt AS firstObservedAt,
                   entity.lastObservedAt AS lastObservedAt,
                   size([x IN files WHERE x IS NOT NULL]) AS sourceCount,
                   size([x IN devices WHERE x IS NOT NULL]) AS deviceCount,
                   entity.communityId AS communityId, entity.bridgeScore AS bridgeScore,
                   coalesce(entity.hasWarnings, false) AS hasWarnings,
                   coalesce(entity.hasContradictions, false) AS hasContradictions,
                   properties(entity) AS properties
            ORDER BY entity.id SKIP $offset LIMIT $fetch_limit
        """, case_id=case_id, entity_id=entity_id,
             entity_types=filters.get("entity_types", []),
             community_id=filters.get("community_id"),
             search=filters.get("search"),
             warning_status=filters.get("warning_status"),
             device_id=filters.get("device_id"),
             source_file_id=filters.get("source_file_id"), minimum=minimum,
             offset=offset, fetch_limit=limit + 1)
        has_more, nodes = len(nodes) > limit, nodes[:limit]
        edges = self.edges([str(n["id"]) for n in nodes], minimum, limit * 4, filters)
        next_cursor = encode_cursor(offset + limit) if has_more else None
        return self._response(case_id, nodes, edges, has_more, next_cursor)

    def entity(self, case_id, entity_id):
        rows = self.run("""
            MATCH (entity:CanonicalEntity {id: $entity_id})
            WHERE entity.caseId = $case_id OR $case_id IN coalesce(entity.caseIds, [])
            OPTIONAL MATCH (entity)-[:SUPPORTED_BY|DERIVED_FROM]->(record:EvidenceRecord)
            WITH entity, collect(DISTINCT record) AS records
            OPTIONAL MATCH (entity)-[rel]-()
            RETURN entity.id AS id, coalesce(entity.type, 'ENTITY') AS type,
                   coalesce(entity.displayLabel, entity.label, entity.name, entity.id) AS label,
                   entity.confidence AS confidence,
                   entity.firstObservedAt AS firstObservedAt,
                   entity.lastObservedAt AS lastObservedAt,
                   [r IN records WHERE r.fileId IS NOT NULL | r.fileId] AS sourceFiles,
                   [r IN records WHERE r.deviceId IS NOT NULL | r.deviceId] AS devices,
                   size(records) AS supportingRecordCount,
                   count(DISTINCT rel) AS relationshipCount,
                   coalesce(entity.hasWarnings, false) AS hasWarnings,
                   coalesce(entity.hasContradictions, false) AS hasContradictions,
                   entity.classification AS classification, properties(entity) AS attributes
        """, case_id=case_id, entity_id=entity_id)
        return rows[0] if rows else None

    def evidence(self, match_clause, case_id, object_id, limit):
        return self.run(f"""
            {match_clause}
            WHERE record.caseId = $case_id OR $case_id IN coalesce(record.caseIds, [])
            RETURN record.id AS id, record.fileId AS fileId,
                   record.deviceId AS deviceId, record.recordId AS recordId,
                   record.evidenceSetId AS evidenceSetId, record.recordType AS recordType,
                   record.extractedText AS extractedText,
                   record.extractedMetadataJson AS extractedMetadata,
                   record.sourceSpan AS sourceSpan, record.startOffset AS startOffset,
                   record.endOffset AS endOffset,
                   record.extractionMethod AS extractionMethod,
                   record.confidence AS confidence, record.observedAt AS observedAt,
                   coalesce(record.contentProtected, true) AS contentProtected,
                   properties(record) AS properties
            ORDER BY record.observedAt LIMIT $limit
        """, case_id=case_id, object_id=object_id, limit=limit)

    def entity_records(self, case_id, entity_id, limit):
        return self.evidence("MATCH (:CanonicalEntity {id: $object_id})-[:SUPPORTED_BY|DERIVED_FROM]->(record:EvidenceRecord)", case_id, entity_id, limit)

    def relationship_evidence(self, case_id, relationship_id, limit):
        return self.evidence("MATCH (record:EvidenceRecord)-[:SUPPORTS]->(:RelationshipEvidence {relationshipId: $object_id})", case_id, relationship_id, limit)

    def merge_history(self, case_id, entity_id, limit):
        return self.run("""
            MATCH (entity:CanonicalEntity {id: $entity_id})<-[:RESULTED_IN]-(merge:EntityMerge)
            WHERE entity.caseId = $case_id OR $case_id IN coalesce(entity.caseIds, [])
            RETURN merge.id AS mergeId, merge.candidateId AS candidateId,
                   merge.status AS status, merge.decidedBy AS decidedBy,
                   merge.decidedAt AS decidedAt, merge.reversible AS reversible,
                   merge.reversedAt AS reversedAt, properties(merge) AS properties
            ORDER BY merge.decidedAt DESC LIMIT $limit
        """, case_id=case_id, entity_id=entity_id, limit=limit)

    def relationship(self, case_id, relationship_id):
        rows = self.run("""
            MATCH (source:CanonicalEntity)-[rel]->(target:CanonicalEntity)
            WHERE rel.id = $relationship_id
              AND (source.caseId = $case_id OR $case_id IN coalesce(source.caseIds, []))
              AND (target.caseId = $case_id OR $case_id IN coalesce(target.caseIds, []))
            OPTIONAL MATCH (record:EvidenceRecord)-[:SUPPORTS]->(p:RelationshipEvidence)
            WHERE p.relationshipId = rel.id
            RETURN rel.id AS id, type(rel) AS type, source.id AS source,
                   target.id AS target, coalesce(rel.confidence, 1.0) AS confidence,
                   coalesce(rel.assertionType, 'EXPLICIT') AS assertionType,
                   rel.extractionMethod AS extractionMethod, true AS directed,
                   properties(rel) AS attributes,
                   {validFrom: rel.validFrom, validTo: rel.validTo,
                    firstObservedAt: rel.firstObservedAt,
                    lastObservedAt: rel.lastObservedAt,
                    precision: coalesce(rel.temporalPrecision, 'SECOND')} AS temporal,
                   count(DISTINCT record) AS evidenceCount,
                   collect(DISTINCT record.fileId) AS sourceFiles,
                   collect(DISTINCT record.deviceId) AS devices,
                   coalesce(rel.hasWarnings, false) AS hasWarnings,
                   coalesce(rel.hasContradictions, false) AS hasContradictions,
                   rel.classification AS classification
        """, case_id=case_id, relationship_id=relationship_id)
        return rows[0] if rows else None

    def timeline(self, case_id, start, end, limit):
        return self.run("""
            MATCH (source:CanonicalEntity)-[rel]->(target:CanonicalEntity)
            WHERE (source.caseId = $case_id OR $case_id IN coalesce(source.caseIds, []))
              AND (target.caseId = $case_id OR $case_id IN coalesce(target.caseIds, []))
              AND rel.id IS NOT NULL AND rel.firstObservedAt IS NOT NULL
              AND toString(rel.firstObservedAt) <= $end
              AND toString(coalesce(rel.lastObservedAt, rel.firstObservedAt)) >= $start
            RETURN rel.id AS relationshipId, type(rel) AS relationshipType,
                   source.id AS source, target.id AS target,
                   rel.firstObservedAt AS firstObservedAt,
                   rel.lastObservedAt AS lastObservedAt,
                   rel.validFrom AS validFrom, rel.validTo AS validTo,
                   coalesce(rel.temporalPrecision, 'SECOND') AS precision,
                   rel.confidence AS confidence
            ORDER BY rel.firstObservedAt LIMIT $limit
        """, case_id=case_id, start=start, end=end, limit=limit)

    def communities(self, case_id, limit):
        return self.run("""
            MATCH (entity:CanonicalEntity)
            WHERE entity.id IS NOT NULL
              AND (entity.caseId = $case_id OR $case_id IN coalesce(entity.caseIds, []))
              AND entity.communityId IS NOT NULL
            WITH entity.communityId AS communityId,
                 collect({id: entity.id, type: coalesce(entity.type, 'ENTITY'),
                          label: coalesce(entity.displayLabel, entity.label,
                                          entity.name, entity.id)}) AS members
            RETURN communityId, size(members) AS memberCount, members
            ORDER BY memberCount DESC LIMIT $limit
        """, case_id=case_id, limit=limit)

    def bridges(self, case_id, limit, minimum):
        return self.run("""
            MATCH (entity:CanonicalEntity)
            WHERE entity.id IS NOT NULL
              AND (entity.caseId = $case_id OR $case_id IN coalesce(entity.caseIds, []))
              AND coalesce(entity.bridgeScore, 0) >= $minimum
            RETURN entity.id AS id, coalesce(entity.type, 'ENTITY') AS type,
                   coalesce(entity.displayLabel, entity.label, entity.name, entity.id) AS label,
                   entity.bridgeScore AS bridgeScore,
                   entity.betweennessCentrality AS betweennessCentrality,
                   entity.communityId AS communityId,
                   coalesce(entity.hasWarnings, false) AS hasWarnings,
                   coalesce(entity.hasContradictions, false) AS hasContradictions,
                   properties(entity) AS properties
            ORDER BY entity.bridgeScore DESC LIMIT $limit
        """, case_id=case_id, limit=limit, minimum=minimum)
