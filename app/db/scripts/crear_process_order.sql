CREATE TABLE process_order (
    process_order_id INT PRIMARY KEY
);

ALTER TABLE job
ADD process_order_id INT NULL;

ALTER TABLE process
ADD process_order_id INT NULL;

ALTER TABLE job
ADD CONSTRAINT FK_job_process_order
FOREIGN KEY (process_order_id) REFERENCES process_order(process_order_id);

ALTER TABLE process
ADD CONSTRAINT FK_process_process_order
FOREIGN KEY (process_order_id) REFERENCES process_order(process_order_id);
