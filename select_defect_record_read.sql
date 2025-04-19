SELECT   dr.defect_record_id,
         j.job_code, p.product_name,
         userinspector.first_name,
         userissue.first_name,
         i.issue_description,
         cp.correction_process_description,
         s.status_name,
         pr.process_name 
FROM defect_record dr
   JOIN job j ON j.job_id = dr.job_id
   JOIN product p ON p.product_id = dr.product_id
   JOIN user userinspector ON userinspector.user_id = dr.inspector_user_id
   JOIN user userissue ON userissue.user_id = dr.issue_by_user_id
   JOIN issue i ON i.issue_id = dr.issue_id
   JOIN process pr ON pr.process_id = i.process_id
   JOIN correction_process cp ON cp.correction_process_id = dr.correction_process_id
   JOIN status s ON s.status_id = dr.status_id
WHERE
   j.job_code LIKE "VA3300-001"
   AND p.product_name LIKE "TANKS"