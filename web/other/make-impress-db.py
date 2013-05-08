#id
#name
#password
#mark-up

import sqlite3

conn = sqlite3.connect("impress.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE impress
                  (Id integer primary key autoincrement, Name, Password, Rst) 
               """)
conn.commit()

"""
INSERT INTO impress(Name, Password, Rst)
VALUES("Demo of lots of stuff", "123", "hello");
.quit
"""
