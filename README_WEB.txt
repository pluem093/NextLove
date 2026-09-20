NEXTLOVE - WEB READY
=====================

ระบบ: Flask + MySQL
ฐานข้อมูล: database.sql
รูปสินค้า/หลักฐาน: static/uploads/

รันบน Windows + XAMPP
1) Start MySQL ใน XAMPP
2) สร้างฐานข้อมูลชื่อ nextlove และ Import database.sql
3) คัดลอก .env.example เป็น .env
4) เปิด Terminal ในโฟลเดอร์นี้
5) pip install -r requirements.txt
6) python app.py
7) เปิด http://127.0.0.1:5000

เผยแพร่เป็นเว็บไซต์ออนไลน์
- ต้องมี Hosting/Cloud ที่รัน Python Flask และมี MySQL ออนไลน์
- ตั้งค่าตัวแปร DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME และ SECRET_KEY
- ตั้ง Start Command เป็น: gunicorn app:app
- Import database.sql เข้าฐานข้อมูลออนไลน์ก่อน
- อย่าใช้ SECRET_KEY ตัวอย่างใน production

หมายเหตุ
- PromptPay ในรุ่นนี้เป็นขั้นตอนจำลองสำหรับโครงงาน ยังไม่เชื่อม Payment Gateway จริง
- ก่อนเปิดใช้งานสาธารณะ ควรเพิ่ม password hashing, CSRF protection, rate limiting และระบบชำระเงินจริง


ระบบตะกร้าสินค้า: เพิ่มสินค้า, เพิ่ม/ลดจำนวน, ลบสินค้า, คำนวณยอดรวม และไปชำระเงิน ใช้ database_cart_update.sql สำหรับฐานข้อมูล nextlove ที่สร้างไว้ก่อนหน้า
