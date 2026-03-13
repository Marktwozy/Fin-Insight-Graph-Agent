EXPAND_ENTITY_NEIGHBORHOOD = """
MATCH (company:Company {entity_id: $entity_id, batch_id: $batch_id})-[:AFFECTS]->(event:Event)
OPTIONAL MATCH (event)-[:BELONGS_TO_TOPIC]->(topic:Topic)
OPTIONAL MATCH (peer:Company {batch_id: $batch_id})-[:AFFECTS]->(event)
WITH company,
     event,
     topic,
     [
         peer_id IN collect(DISTINCT peer.entity_id)
         WHERE peer_id IS NOT NULL AND peer_id <> company.entity_id
     ] AS related_entity_ids
RETURN company.entity_id AS entity_id,
       company.ticker AS ticker,
       event.event_id AS event_id,
       event.name AS event_name,
       topic.name AS topic_name,
       related_entity_ids
LIMIT $limit
"""