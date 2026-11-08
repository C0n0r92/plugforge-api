-- A mutable original URL can have multiple payload editions or archive captures.
-- Task identity, not URL alone, is unique. Preserve all prior checkpoints.
CREATE TABLE IF NOT EXISTS work_queue_versioned(task_id TEXT PRIMARY KEY,roll TEXT REFERENCES school,stage TEXT NOT NULL,source_url TEXT,document_id TEXT REFERENCES document,status TEXT NOT NULL,priority INTEGER NOT NULL,checkpoint_json TEXT NOT NULL,updated_at TEXT);
INSERT OR IGNORE INTO work_queue_versioned SELECT * FROM work_queue;
DROP TABLE work_queue;
ALTER TABLE work_queue_versioned RENAME TO work_queue;
CREATE INDEX IF NOT EXISTS idx_queue_status ON work_queue(stage,status,priority);
