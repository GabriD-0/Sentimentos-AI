import psycopg2
import os
import threading
import time
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from transformers import pipeline
from datetime import datetime

load_dotenv()

DB_CFG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "postgres"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

sentiment_pipe = pipeline(
    "text-classification",
    model="pysentimiento/bertweet-pt-sentiment",
    tokenizer="pysentimiento/bertweet-pt-sentiment",
    device=-1 # -1 = CPU, 0 = primeira GPU
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

@app.route("/metrics")
def metrics():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                DATE_TRUNC(
                    'day',
                    data_envio AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo'
                ) AS dia,
                sentimento,
                COUNT(*)::INT
            FROM mensagens
            WHERE data_envio >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '4 days'
            GROUP BY dia, sentimento
            ORDER BY dia
        """)
        daily_raw = cur.fetchall()

        from collections import defaultdict
        daily = defaultdict(lambda: {"positive": 0, "negative": 0})
        for dia, sent, qtd in daily_raw:
            s = (sent or "").lower()
            if s.startswith("pos"):
                daily[dia]["positive"] = qtd
            elif s.startswith("neg"):
                daily[dia]["negative"] = qtd

        cur.execute("""
            SELECT
                DATE_TRUNC(
                    'hour',
                    data_envio AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo'
                ) AS hora,
                sentimento,
                COUNT(*)::INT
            FROM mensagens
            WHERE data_envio >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '24 hours'
            GROUP BY hora, sentimento
            ORDER BY hora
        """)
        hourly_raw = cur.fetchall()

        hourly = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
        for hora, sent, qtd in hourly_raw:
            s = (sent or "").lower()
            if s.startswith("pos"):
                hourly[hora]["positive"] = qtd
            elif s.startswith("neg"):
                hourly[hora]["negative"] = qtd
            else:
                hourly[hora]["neutral"] = qtd

        # C) Pizza – totais gerais
        cur.execute("""
            SELECT sentimento, COUNT(*)::INT
            FROM mensagens
            GROUP BY sentimento
        """)
        overall = { (row[0] or "").lower(): row[1] for row in cur.fetchall() }

    # serialização (string) para JSON
    daily_serial  = [
        {"day": dia.strftime("%Y-%m-%d"), **vals}
        for dia, vals in sorted(daily.items())
    ]
    hourly_serial = [
        {"hour": hora.strftime("%H:%M"), **vals}
        for hora, vals in sorted(hourly.items())
    ]

    return jsonify({
        "daily":   daily_serial,
        "hourly":  hourly_serial,
        "overall": overall,
    })


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


def classify_unlabeled(interval: int = 120):
    while True:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, mensagem FROM mensagens WHERE sentimento IS NULL;")
            rows = cur.fetchall()

            if not rows:
                time.sleep(interval)
                continue

            ids_atualizados = []
            for msg_id, texto in rows:
                label = sentiment_pipe(texto, truncation=True)[0]["label"]

                cur.execute(
                    """
                    UPDATE mensagens
                    SET sentimento = %s
                    WHERE id = %s
                    AND sentimento IS NULL;
                    """,
                    (label, msg_id),
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
