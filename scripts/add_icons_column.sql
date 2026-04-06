-- [MIGRATION] Add icon column to base_items
ALTER TABLE base_items ADD COLUMN IF NOT EXISTS icon VARCHAR(255);

-- [SEEDING] Map existing Peasant and Ranger sets to icons
-- Assuming icons will be generated and stored in /static/icons/gear/

-- Hoods
UPDATE base_items SET icon = '/static/icons/gear/hood_ranger.png' WHERE slot = 'HEAD' AND name ILIKE '%Ranger%';

-- Body / Tunic
UPDATE base_items SET icon = '/static/icons/gear/tunic_peasant.png' WHERE slot = 'BODY' AND name ILIKE '%Peasant%';
UPDATE base_items SET icon = '/static/icons/gear/tunic_ranger.png' WHERE slot = 'BODY' AND name ILIKE '%Ranger%';

-- ARMS (Bracers)
UPDATE base_items SET icon = '/static/icons/gear/bracers_peasant.png' WHERE slot = 'ARMS' AND name ILIKE '%Peasant%';
UPDATE base_items SET icon = '/static/icons/gear/bracers_ranger.png' WHERE slot = 'ARMS' AND name ILIKE '%Ranger%';

-- LEGS (Trousers)
UPDATE base_items SET icon = '/static/icons/gear/legs_peasant.png' WHERE slot = 'LEGS' AND name ILIKE '%Peasant%';
UPDATE base_items SET icon = '/static/icons/gear/legs_ranger.png' WHERE slot = 'LEGS' AND name ILIKE '%Ranger%';

-- FEET (Boots)
UPDATE base_items SET icon = '/static/icons/gear/boots_peasant.png' WHERE slot = 'FEET' AND name ILIKE '%Peasant%';
UPDATE base_items SET icon = '/static/icons/gear/boots_ranger.png' WHERE slot = 'FEET' AND name ILIKE '%Ranger%';

-- ACC (Pauldrons)
UPDATE base_items SET icon = '/static/icons/gear/pauldrons_ranger.png' WHERE slot = 'ACC' AND name ILIKE '%Ranger%';
