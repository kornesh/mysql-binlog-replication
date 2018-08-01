# Streaming mysql binlog replication to Snowflake


In Snowflakes web interface run this query to create a database and table
```sql
CREATE OR REPLACE DATABASE testdb;
USE DATABASE testdb;
CREATE OR REPLACE TABLE testtbl(id integer, name string);
```

You can use the following python script to generate Snowflake compatible schema
```bash
 docker-compose exec python python mysql2snowsql.py
```

Clone this repo and update your Snowflake credentials in `example.env`, then
```bash
mv example.env .env
docker-compose up --build
```

Note: If you get `Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)` error on the first run, try running it again.

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

# References
- https://www.alooma.com/blog/mysql-to-amazon-redshift-replication
- https://aws.amazon.com/blogs/database/streaming-changes-in-a-database-with-amazon-kinesis/
- https://github.com/danfengcao/binlog2sql
- https://www.thegeekstuff.com/2017/08/mysqlbinlog-examples/