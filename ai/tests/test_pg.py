import os
from pprint import pprint
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_CFG = dict(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    )

print("Tentando conectar com parâmetros:")
pprint({k: ("***" if k == "password" else v) for k, v in DB_CFG.items()})
print("----------------------------------------------------------")

try:
    if psycopg2:
        conn = psycopg2.connect(**DB_CFG)

    with conn, conn.cursor() as cur:
        cur.execute("SELECT 1;")
        print("Conexão OK – resultado:", cur.fetchone())

except Exception as exc:
    print("Falhou ao conectar:")
    print(exc)

finally:
    try:
        conn.close()
    except Exception:
        pass