# Streaming mysql binlog replication to Redshift


Run this query on Redshift to create a new table
```sql
    DROP TABLE IF EXISTS testtbl;
    CREATE TABLE testtbl(id integer, name varchar(255));
```

Clone this repo and update your Redshift credentials in `example.env`, then
```bash
cd redshift/
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
![Redshift History showing slow queries](https://i.imgur.com/r4vVhHL.png)

# References
- https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_30.html
- https://docs.aws.amazon.com/redshift/latest/dg/t_Updating_tables_with_DML_commands.html
- https://docs.aws.amazon.com/redshift/latest/dg/c_redshift-and-postgres-sql.html
- https://www.blendo.co/blog/access-your-data-in-amazon-redshift-and-postgresql-with-python-and-r/