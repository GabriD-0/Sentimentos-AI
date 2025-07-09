from datetime import datetime
import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask, jsonify
import psycopg2
from transformers import pipeline

load_dotenv()

DB_CFG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "postgres"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

from transformers import pipeline

sentiment_pipe = pipeline(
    "text-classification",
    model="pysentimiento/bertweet-pt-sentiment",  # ou outro
    tokenizer="pysentimiento/bertweet-pt-sentiment",
    device=-1                 # -1 = CPU, 0 = primeira GPU
)


def get_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(**DB_CFG)

app = Flask(__name__)

@app.route("/mensagens")
def mensagens():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM mensagens;")
        cols = [c[0] for c in cur.description]
        return jsonify([dict(zip(cols, row)) for row in cur.fetchall()])

def classify_unlabeled(interval: int = 120):
    while True:
        with get_conn() as conn, conn.cursor() as cur:
            # 1. Obtém mensagens sem sentimento
            cur.execute("SELECT id, mensagem FROM mensagens WHERE sentimento IS NULL;")
            rows = cur.fetchall()

            if not rows:
                time.sleep(interval)
                continue  # nada para fazer

            ids_atualizados = []
            for msg_id, texto in rows:
                # 2) classifica
                label = sentiment_pipe(texto, truncation=True)[0]["label"]

                # 3) PATCH – atualiza só se continuar NULL
                cur.execute(
                    """
                    UPDATE mensagens
                    SET sentimento = %s
                    WHERE id = %s
                    AND sentimento IS NULL;
                    """,
                    (label, msg_id),   # tuple de parâmetros
                )

                if cur.rowcount:
                    ids_atualizados.append(msg_id)

            conn.commit()

        if ids_atualizados:
            print(
                f"[{datetime.now():%H:%M:%S}] Sentimento adicionado em "
                f"{len(ids_atualizados)} mensagem(ns): {ids_atualizados}"
            )

        time.sleep(interval)

if __name__ == "__main__":
    threading.Thread(target=classify_unlabeled, daemon=True).start()
    app.run(debug=True, port=5000)
