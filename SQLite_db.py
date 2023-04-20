import sqlite3 as sq

async def db_connect() -> None:
    global db, cur 
    
    db = sq.connect('requests.db')
    cur = db.cursor()
    
    cur.execute("CREATE TABLE IF NOT EXISTS request(req_id INTEGER PRIMARY KEY, problem TEXT, adress TEXT, phone TEXT, user_id TEXT)")
    db.commit()
    
async def get_all_requests():

    reqs = cur.execute("SELECT * FROM request").fetchall()

    return reqs #list