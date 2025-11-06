CREATE DATABASE IF NOT EXISTS kims_ordering_system CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE kims_ordering_system;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    user_email VARCHAR(120) NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(200),
    postal VARCHAR(20),
    city VARCHAR(100),
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    items TEXT,
    total DECIMAL(10,2),
    payment_method VARCHAR(50),
    payment_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Processing'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
