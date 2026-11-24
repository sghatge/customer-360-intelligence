-- Query 1: high-value customers with email consent
SELECT crm_id, name, tier, ltv
FROM profiles
WHERE ltv >= 30000
  AND email_ok = 1
ORDER BY ltv DESC;

-- Query 2: cart events enriched with profile attributes
SELECT e.event_id, e.product, p.name, p.email
FROM events AS e
JOIN profiles AS p ON p.crm_id = e.crm_id
WHERE e.event_type = 'add_to_cart';

-- Query 3: event volume by event type
SELECT event_type, COUNT(*) AS event_count
FROM events
GROUP BY event_type
ORDER BY event_count DESC;

-- Query 4: profiles with no recent activity
SELECT crm_id, name, last_seen
FROM profiles
WHERE last_seen >= 30
ORDER BY last_seen DESC;
