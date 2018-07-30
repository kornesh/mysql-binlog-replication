# Streaming mysql binlog replication to Snowflake/Redshift/BigQuery

```bash
docker-compose up --build
```

In another terminal login into the mysql instance
```bash
docker-compose exec mysql mysql -u root -pexample
```
And execute the following
```sql
DROP DATABASE IF EXISTS testdb;
CREATE DATABASE testdb; USE testdb;
CREATE TABLE testtbl (id int);
INSERT INTO testtbl VALUES (1), (2), (3), (1);
DELETE FROM testtbl WHERE id = 1;
SELECT * FROM testtbl;
```

Or you can just
```bash
docker-compose exec mysql mysql -u root -pexample -e "DROP DATABASE IF EXISTS testdb; CREATE DATABASE testdb; USE testdb; CREATE TABLE testtbl (id int); INSERT INTO testtbl VALUES (1), (2), (3), (1); DELETE FROM testtbl WHERE id = 1; SELECT * FROM testtbl;"
```

Which will output the following to the terminal
```
+------+
| id   |
+------+
|    2 |
|    3 |
+------+
```

`docker-compose` daemon should output something like this
```sql
python_1  | INSERT INTO `testdb`.`testtbl`(`id`) VALUES (1);
python_1  | {"row": {"values": {"id": 2}}, "schema": "testdb", "table": "testtbl", "type": "WriteRowsEvent"}
python_1  | INSERT INTO `testdb`.`testtbl`(`id`) VALUES (2);
python_1  | {"row": {"values": {"id": 3}}, "schema": "testdb", "table": "testtbl", "type": "WriteRowsEvent"}
python_1  | INSERT INTO `testdb`.`testtbl`(`id`) VALUES (3);
python_1  | {"row": {"values": {"id": 1}}, "schema": "testdb", "table": "testtbl", "type": "WriteRowsEvent"}
python_1  | INSERT INTO `testdb`.`testtbl`(`id`) VALUES (1);
python_1  | {"row": {"values": {"id": 1}}, "schema": "testdb", "table": "testtbl", "type": "DeleteRowsEvent"}
python_1  | DELETE FROM `testdb`.`testtbl` WHERE `id`=1 LIMIT 1;
python_1  | {"row": {"values": {"id": 1}}, "schema": "testdb", "table": "testtbl", "type": "DeleteRowsEvent"}
python_1  | DELETE FROM `testdb`.`testtbl` WHERE `id`=1 LIMIT 1;
```

# References
- https://www.alooma.com/blog/mysql-to-amazon-redshift-replication
- https://aws.amazon.com/blogs/database/streaming-changes-in-a-database-with-amazon-kinesis/
- https://github.com/danfengcao/binlog2sql