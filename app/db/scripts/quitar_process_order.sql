ALTER TABLE job
DROP CONSTRAINT FK_job_process_order;

ALTER TABLE process
DROP CONSTRAINT FK_process_process_order;

ALTER TABLE job
DROP COLUMN process_order_id;

ALTER TABLE process
DROP COLUMN process_order_id;

DROP TABLE process_order;
