# Streaming mysql binlog replication to BigQuery
[![](https://images.microbadger.com/badges/image/servicerocket/mysql2bigquery.svg)](https://hub.docker.com/r/servicerocket/mysql2bigquery/)

Generate a [JSON service account](https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python) credentials file and copy it to `bigquery/` directory and mount the file from `docker-compose.yml`. 

Clone this repo and update your GCP `PROJECT_ID` and `GOOGLE_APPLICATION_CREDENTIALS` location in `example.env`, then
```bash
cd bigquery/
mv example.env .env
docker-compose up --build
```

> Note: If you get `Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)` error on the first run, try running it again.

In another terminal run
```bash
docker-compose exec mysql mysql -u root -pexample -e "DROP DATABASE IF EXISTS testdb; CREATE DATABASE testdb; USE testdb; CREATE TABLE testtbl (id int, name varchar(255)); INSERT INTO testtbl VALUES (1, 'hello'), (2, 'hola'), (3, 'zdravstvuy'), (1, 'bonjour'); UPDATE testtbl SET name = 'yolo' WHERE id = 1; UPDATE testtbl SET name = 'world' WHERE id = 3; DELETE FROM testtbl WHERE id = 1; SELECT * FROM testtbl;"
```

Which will output the following to the terminal
```
+------+-------+
| id   | name  |
+------+-------+
|    2 | hola  |
|    3 | world |
+------+-------+
```

`docker-compose` daemon should output something like this
```sql
python_1  | INSERT INTO testtbl(name, id) VALUES ('hello', 1);
python_1  | INSERT INTO testtbl(name, id) VALUES ('hola', 2);
python_1  | INSERT INTO testtbl(name, id) VALUES ('zdravstvuy', 3);
python_1  | INSERT INTO testtbl(name, id) VALUES ('bonjour', 1);
python_1  | UPDATE testtbl SET name='yolo', id=1 WHERE name='hello' AND id=1;
python_1  | UPDATE testtbl SET name='yolo', id=1 WHERE name='bonjour' AND id=1;
python_1  | UPDATE testtbl SET name='world', id=3 WHERE name='zdravstvuy' AND id=3;
python_1  | DELETE FROM testtbl WHERE name='yolo' AND id=1;
python_1  | DELETE FROM testtbl WHERE name='yolo' AND id=1;
```
Executing these queries one by one is not optimal. Ideally, we should batch them together.

# References
- https://googlecloudplatform.github.io/google-cloud-python/latest/bigquery/usage.html
- https://cloud.google.com/bigquery/streaming-data-into-bigquery