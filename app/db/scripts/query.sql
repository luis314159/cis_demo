SELECT *
FROM job j
JOIN defect_record dr ON dr.job_id = j.job_id
JOIN status s ON s.status_id = dr.status_id
              AND s.status_name NOT LIKE '%Ok%'
WHERE j.job_code = 'VA325E-001'


