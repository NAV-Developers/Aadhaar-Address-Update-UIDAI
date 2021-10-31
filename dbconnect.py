from dns.resolver import query
import mysql.connector as connector

con = connector.connect(host='localhost',
                user='root',
            password='jesus10*',
            database='aadhaar')

query = 'create table if not exists chat(hash varchar(400) primary key)'
cur = con.cursor()
cur.execute(query)
print("Created")

query = 'insert into chat values("bebc6d778d79b152f0e382c7379dd4f183f122386a75aa0f26a7e162fc8acde3")'
print(query)
cur = con.cursor()
cur.execute(query)
cur.close()
con.commit()
print("Message Hash Saved To The Chat DB")

# helper = DBHelper()
# helper.insert_chat("bebc6d778d79b152f0e382c7379dd4f183f122386a75aa0f26a7e162fc8acde3")