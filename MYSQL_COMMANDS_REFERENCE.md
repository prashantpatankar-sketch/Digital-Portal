# 📚 MySQL Commands Quick Reference for Django Developers

## Database Management

### Create Database

```sql
-- Basic
CREATE DATABASE gram_panchayat_db;

-- With charset (RECOMMENDED for Django)
CREATE DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- View charset
SHOW CREATE DATABASE gram_panchayat_db;
```

### Drop Database

```sql
DROP DATABASE gram_panchayat_db;
```

### List All Databases

```sql
SHOW DATABASES;
```

### Select Database

```sql
USE gram_panchayat_db;
```

---

## User Management

### Create User

```sql
-- Create user with password
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'password123';

-- Create user with no password
CREATE USER 'django_user'@'localhost';

-- Create user from any host
CREATE USER 'django_user'@'%' IDENTIFIED BY 'password123';
```

### Grant Privileges

```sql
-- All privileges on one database
GRANT ALL PRIVILEGES ON gram_panchayat_db.* TO 'django_user'@'localhost';

-- Specific privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON gram_panchayat_db.* TO 'django_user'@'localhost';

-- Only SELECT privilege
GRANT SELECT ON gram_panchayat_db.* TO 'django_user'@'localhost';

-- All privileges, all databases
GRANT ALL PRIVILEGES ON *.* TO 'django_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;
```

### View User Privileges

```sql
-- List all users
SELECT User, Host FROM mysql.user;

-- Show privileges for specific user
SHOW GRANTS FOR 'django_user'@'localhost';
```

### Change Password

```sql
-- Set new password
ALTER USER 'django_user'@'localhost' IDENTIFIED BY 'new_password';

-- Or
SET PASSWORD FOR 'django_user'@'localhost' = 'new_password';

-- Apply changes
FLUSH PRIVILEGES;
```

### Drop User

```sql
DROP USER 'django_user'@'localhost';
```

### Revoke Privileges

```sql
-- Remove all privileges
REVOKE ALL PRIVILEGES ON gram_panchayat_db.* FROM 'django_user'@'localhost';

-- Remove specific privilege
REVOKE SELECT ON gram_panchayat_db.* FROM 'django_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;
```

---

## Table Management

### Show Tables

```sql
-- In selected database
SHOW TABLES;

-- Show table structure
DESCRIBE auth_user;
-- OR
SHOW COLUMNS FROM auth_user;
```

### Create Table

```sql
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Modify Table

```sql
-- Add column
ALTER TABLE posts ADD COLUMN status VARCHAR(20);

-- Drop column
ALTER TABLE posts DROP COLUMN status;

-- Rename column
ALTER TABLE posts RENAME COLUMN status TO post_status;

-- Change column type
ALTER TABLE posts MODIFY COLUMN title VARCHAR(300);
```

### Drop Table

```sql
DROP TABLE posts;
```

### Truncate Table (Delete all data)

```sql
-- Delete all data, reset auto_increment
TRUNCATE TABLE posts;
```

---

## Data Queries

### Select Data

```sql
-- All columns
SELECT * FROM auth_user;

-- Specific columns
SELECT id, username, email FROM auth_user;

-- With conditions
SELECT * FROM auth_user WHERE is_active = 1;

-- With limit
SELECT * FROM auth_user LIMIT 10;

-- With offset
SELECT * FROM auth_user LIMIT 10 OFFSET 20;

-- Count rows
SELECT COUNT(*) FROM auth_user;

-- Order by
SELECT * FROM auth_user ORDER BY username ASC;

-- Group by
SELECT is_active, COUNT(*) FROM auth_user GROUP BY is_active;
```

### Insert Data

```sql
INSERT INTO auth_user (username, email, password) 
VALUES ('john', 'john@example.com', 'hashed_password');
```

### Update Data

```sql
-- Update specific row
UPDATE auth_user SET email = 'newemail@example.com' WHERE username = 'john';

-- Update multiple columns
UPDATE auth_user SET email = 'new@example.com', is_active = 0 WHERE id = 1;
```

### Delete Data

```sql
-- Delete specific row
DELETE FROM auth_user WHERE username = 'john';

-- Delete multiple rows
DELETE FROM auth_user WHERE is_active = 0;

-- ⚠️ DELETE ALL DATA IN TABLE (be careful!)
DELETE FROM auth_user;
```

---

## Backup & Restore

### Backup Database

```bash
# Backup entire database
mysqldump -u root -p gram_panchayat_db > backup.sql

# Backup specific tables
mysqldump -u root -p gram_panchayat_db auth_user auth_group > users_groups_backup.sql

# Backup all databases
mysqldump -u root -p --all-databases > all_backup.sql

# Backup with timestamp
mysqldump -u root -p gram_panchayat_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
mysql -u root -p gram_panchayat_db < backup.sql

# Restore to new database
mysql -u root -p < backup.sql
# (if backup contains CREATE DATABASE)
```

---

## Database Status

### Show Variables

```sql
-- Show all variables
SHOW VARIABLES;

-- Show specific variable
SHOW VARIABLES LIKE 'max_connections';

-- Common variables
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';
SHOW VARIABLES LIKE 'sql_mode';
```

### Set Variables (Session-only)

```sql
-- Set for current session
SET sql_mode='STRICT_TRANS_TABLES';
SET SESSION max_connections = 1000;

-- Set for all future sessions
SET GLOBAL max_connections = 1000;
```

### Server Status

```sql
-- Show server status
SHOW STATUS;

-- Specific status
SHOW STATUS LIKE 'Threads%';

-- Database size
SELECT 
    SUM(data_length + index_length) / 1024 / 1024 AS size_mb
FROM information_schema.tables
WHERE table_schema = 'gram_panchayat_db';

-- Table sizes
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'gram_panchayat_db'
ORDER BY size_mb DESC;
```

---

## Index Management

### Create Index

```sql
-- Single column index
CREATE INDEX idx_username ON auth_user(username);

-- Multi-column index
CREATE INDEX idx_user_email ON auth_user(username, email);

-- Unique index
CREATE UNIQUE INDEX idx_email ON auth_user(email);
```

### View Indexes

```sql
-- Show all indexes on table
SHOW INDEXES FROM auth_user;

-- Show index details
SHOW INDEX FROM auth_user;
```

### Drop Index

```sql
DROP INDEX idx_username ON auth_user;
```

---

## Transaction Management

### Basic Transactions

```sql
-- Start transaction
START TRANSACTION;

-- Do some work
INSERT INTO auth_user (username, email) VALUES ('test', 'test@example.com');
UPDATE auth_user SET is_active = 1 WHERE id = 5;

-- Commit (save changes)
COMMIT;

-- Or rollback (undo changes)
ROLLBACK;
```

### Savepoints

```sql
START TRANSACTION;

INSERT INTO auth_user (username) VALUES ('user1');

-- Create savepoint
SAVEPOINT sp1;

INSERT INTO auth_user (username) VALUES ('user2');

-- Rollback to savepoint
ROLLBACK TO SAVEPOINT sp1;

-- Commit (only user1 inserted)
COMMIT;
```

---

## Repair & Optimize

### Check Table Integrity

```sql
-- Check single table
CHECK TABLE auth_user;

-- Check all tables in database
CHECK TABLE gram_panchayat_db.*;
```

### Repair Table

```sql
-- Repair single table
REPAIR TABLE auth_user;

-- Repair all tables in database
REPAIR TABLE gram_panchayat_db.*;
```

### Optimize Table

```sql
-- Optimize single table
OPTIMIZE TABLE auth_user;

-- Optimize all tables
OPTIMIZE TABLE gram_panchayat_db.*;
```

### Analyze Table

```sql
-- Analyze single table
ANALYZE TABLE auth_user;

-- Analyze all tables
ANALYZE TABLE gram_panchayat_db.*;
```

---

## Views (Virtual Tables)

### Create View

```sql
CREATE VIEW active_users AS
SELECT id, username, email
FROM auth_user
WHERE is_active = 1;

-- Use it like a table
SELECT * FROM active_users;
```

### Drop View

```sql
DROP VIEW active_users;
```

---

## Stored Procedures (Advanced)

### Create Simple Procedure

```sql
DELIMITER //
CREATE PROCEDURE GetUserCount()
BEGIN
    SELECT COUNT(*) FROM auth_user;
END//
DELIMITER ;

-- Call it
CALL GetUserCount();
```

### Drop Procedure

```sql
DROP PROCEDURE GetUserCount;
```

---

## Django-Specific Queries

### View All Tables Django Created

```sql
SHOW TABLES;

-- Result includes:
-- auth_user, auth_group, auth_user_groups, auth_permission
-- auth_group_permissions, auth_user_user_permissions
-- django_migrations, django_session, django_content_type
-- (and your custom app tables)
```

### Check Django Migrations Applied

```sql
SELECT * FROM django_migrations;

-- Shows all applied migrations with timestamp
```

### View Model Data

```sql
-- If you have a Post model
SELECT * FROM portal_app_post;

-- If you have a User model
SELECT * FROM portal_app_customuser;
```

### Count Data

```sql
SELECT 
    (SELECT COUNT(*) FROM auth_user) as total_users,
    (SELECT COUNT(*) FROM portal_app_post) as total_posts,
    (SELECT COUNT(*) FROM portal_app_complaint) as total_complaints;
```

---

## Encoding & Charset (Important for Django)

### Check Database Charset

```sql
SHOW CREATE DATABASE gram_panchayat_db;
```

### Check Table Charset

```sql
SHOW CREATE TABLE auth_user;
```

### Fix Database Charset

```sql
ALTER DATABASE gram_panchayat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Fix Table Charset

```sql
ALTER TABLE auth_user CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Check Connection Charset

```sql
SHOW VARIABLES LIKE 'character_set%';
```

---

## Common Django Developer Queries

### Find Users

```sql
-- All users
SELECT id, username, email, is_active FROM auth_user;

-- Active users
SELECT * FROM auth_user WHERE is_active = 1;

-- Superusers
SELECT * FROM auth_user WHERE is_superuser = 1;

-- Staff members
SELECT * FROM auth_user WHERE is_staff = 1;
```

### Find Applications

```sql
-- All applications
SELECT * FROM portal_app_application;

-- Pending applications
SELECT * FROM portal_app_application WHERE status = 'pending';

-- Approved applications
SELECT * FROM portal_app_application WHERE status = 'approved';
```

### Find Complaints

```sql
-- All complaints
SELECT * FROM portal_app_complaint;

-- Unresolved complaints
SELECT * FROM portal_app_complaint WHERE status != 'resolved';

-- High priority complaints
SELECT * FROM portal_app_complaint WHERE priority = 'high';
```

### Join Queries

```sql
-- User and their applications
SELECT u.username, a.application_number, a.status
FROM auth_user u
JOIN portal_app_application a ON u.id = a.applicant_id;

-- User and their complaints
SELECT u.username, c.complaint_number, c.status
FROM auth_user u
JOIN portal_app_complaint c ON u.id = c.complainant_id;
```

---

## Quick Login & Test

```bash
# Login to MySQL
mysql -u root -p
# Enter password

# In MySQL:
use gram_panchayat_db;
SHOW TABLES;
SELECT COUNT(*) FROM auth_user;
EXIT;
```

---

## Cheat Sheet Summary

| Task | Command |
|------|---------|
| **Login** | `mysql -u user -p database` |
| **Show databases** | `SHOW DATABASES;` |
| **Create database** | `CREATE DATABASE name;` |
| **Show tables** | `SHOW TABLES;` |
| **Show data** | `SELECT * FROM table;` |
| **Count rows** | `SELECT COUNT(*) FROM table;` |
| **Backup** | `mysqldump -u user -p db > file.sql` |
| **Restore** | `mysql -u user -p db < file.sql` |
| **Backup with date** | `mysqldump -u user -p db > backup_$(date +%Y%m%d).sql` |

---

**Use these commands alongside Django for database management!** ✅

