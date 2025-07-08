import os
from dotenv import load_dotenv
from flask import Flask, jsonify
import psycopg2

load_dotenv()

DB_CFG = dict(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

def get_conn():
    return psycopg2.connect(**DB_CFG)

app = Flask(__name__)

@app.route("/mensagens")
def mensagens():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM mensagens;")
        cols = [c[0] for c in cur.description]
        data = [dict(zip(cols, row)) for row in cur.fetchall()]
    return jsonify(data)



if __name__ == "__main__":
    app.run(debug=True, port=5000)


#ssh -N -L 5433:localhost:5432 gabriel@168.231.98.84
