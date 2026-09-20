CREATE DATABASE IF NOT EXISTS nextlove CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nextlove;
CREATE TABLE users(
 id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(100) NOT NULL,
 email VARCHAR(150) UNIQUE NOT NULL,password VARCHAR(255) NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE products(
 id INT AUTO_INCREMENT PRIMARY KEY,seller_id INT NOT NULL,name VARCHAR(200) NOT NULL,
 category VARCHAR(100) NOT NULL,description TEXT,size VARCHAR(50),
 condition_text VARCHAR(100),price DECIMAL(10,2) NOT NULL,image VARCHAR(255),
 status ENUM('available','sold') DEFAULT 'available',quantity INT NOT NULL DEFAULT 1,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(seller_id) REFERENCES users(id));
CREATE TABLE orders(
 id INT AUTO_INCREMENT PRIMARY KEY,buyer_id INT NOT NULL,seller_id INT NOT NULL,product_id INT NOT NULL,quantity INT NOT NULL DEFAULT 1,
 total DECIMAL(10,2) NOT NULL,payment_method ENUM('พร้อมเพย์','เก็บเงินปลายทาง') NOT NULL,
 shipping_method VARCHAR(100) NOT NULL,status ENUM('pending','paid','shipped','received','cancelled') DEFAULT 'pending',
 tracking_no VARCHAR(100),created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(buyer_id) REFERENCES users(id),FOREIGN KEY(seller_id) REFERENCES users(id),
 FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE complaints(
 id INT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,type VARCHAR(100) NOT NULL,
 detail TEXT NOT NULL,evidence VARCHAR(255),status ENUM('pending','checking','resolved') DEFAULT 'pending',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE reviews(
 id INT AUTO_INCREMENT PRIMARY KEY,order_id INT NOT NULL,buyer_id INT NOT NULL,
 seller_id INT NOT NULL,rating TINYINT NOT NULL,comment TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE transactions(
 id INT AUTO_INCREMENT PRIMARY KEY,order_id INT NOT NULL,sale_amount DECIMAL(10,2) NOT NULL,
 platform_fee DECIMAL(10,2) NOT NULL,seller_net DECIMAL(10,2) NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
