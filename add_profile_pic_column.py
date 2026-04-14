import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()
DB_HOST=os.getenv('DB_HOST')
DB_USER=os.getenv('DB_USER')
DB_PASSWORD=os.getenv('DB_PASSWORD')
DB_NAME=os.getenv('DB_NAME')
conn=mysql.connector.connect(host=DB_HOST,user=DB_USER,password=DB_PASSWORD,database=DB_NAME)
cur=conn.cursor()
cur.execute("SHOW COLUMNS FROM users LIKE 'profile_pic'")
if cur.fetchone():
    print('profile_pic column already exists.')
else:
    cur.execute("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(255) NULL")
    conn.commit()
    print('profile_pic column added successfully.')
cur.close()
conn.close()
