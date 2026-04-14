CREATE DATABASE IF NOT EXISTS healthcare;
USE healthcare;

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY unique_email (email)
);

-- =========================
-- MEDICINE TABLE
-- =========================
CREATE TABLE medicine (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(500) DEFAULT NULL,
    dose VARCHAR(200) DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'active',
    insert_date DATE DEFAULT (CURDATE()),
    user_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY unique_user_medicine (user_id, name),
    CONSTRAINT fk_medicine_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_status
        CHECK (status IN ('active', 'inactive'))
);

-- =========================
-- REMINDER LOGS TABLE
-- =========================
CREATE TABLE reminder_logs (
    id INT NOT NULL AUTO_INCREMENT,
    medicine_id INT DEFAULT NULL,
    reminder_time TIME DEFAULT NULL,
    day_of_week VARCHAR(20) DEFAULT NULL,
    later_time TIME DEFAULT NULL,
    status ENUM('active','inactive') DEFAULT 'active',
    PRIMARY KEY (id),
    CONSTRAINT fk_reminder_medicine
        FOREIGN KEY (medicine_id) REFERENCES medicine(id)
        ON DELETE CASCADE
);