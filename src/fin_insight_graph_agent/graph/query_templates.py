EXPAND_ENTITY_NEIGHBORHOOD = """
MATCH (company:Company {entity_id: $entity_id, batch_id: $batch_id})-[:AFFECTS]->(event:Event)
OPTIONAL MATCH (event)-[:BELONGS_TO_TOPIC]->(topic:Topic)
RETURN company.entity_id AS entity_id,
       company.ticker AS ticker,
       event.event_id AS event_id,
       event.name AS event_name,
       topic.name AS topic_name
LIMIT $limit
"""