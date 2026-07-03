-- Recommended indexes to improve performance for common queries
-- Run these manually against your RackTables MySQL instance if appropriate.

CREATE INDEX idx_dictionary_chapter_key ON Dictionary(chapter_id, dict_key);
CREATE INDEX idx_attributevalue_obj_attr ON AttributeValue(object_id, attr_id);
CREATE INDEX idx_rackspace_object ON RackSpace(object_id);
CREATE INDEX idx_port_object ON Port(object_id);
CREATE INDEX idx_object_objtype ON Object(objtype_id);
