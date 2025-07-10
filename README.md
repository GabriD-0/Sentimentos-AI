# Sentimentos-AI 🧠💬

**Sentimentos-AI** é um micro-serviço em Flask que:

1. **Coleta mensagens** vindas do *Evolution API* (WhatsApp Cloud) e grava em um
   banco **PostgreSQL**.
2. **Classifica** automaticamente o sentimento/emoção de cada mensagem usando o
   modelo 🇧🇷 **`pysentimiento/bertweet-pt-sentiment`**.
3. Expõe **end-points REST** (`/mensagens`, `/metrics`) e um pequeno
   **dashboard** (`/`) para acompanhar as métricas em tempo real.
```
> Repositório: `Projeto/Sentimentos-AI`  
> Linguagem: **Python 3.12.10+**
```
---

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação](#instalação)
3. [Configurando o `.env`](#configurando-o-env)
4. [Criando as tabelas](#criando-as-tabelas)
5. [Integrando o Evolution API](#integrando-o-evolution-api)
6. [Executando a aplicação](#executando-a-aplicação)
7. [Endpoints & métricas](#endpoints--métricas)
8. [Estrutura do código](#estrutura-do-código)
9. [Próximos passos](#próximos-passos)
10. [Licença](#licença)

---

## Pré-requisitos

| Ferramenta           | Versão recomendada |
|----------------------|--------------------|
| Python               | 3.12 ou superior   |
| PostgreSQL           | ≥ 14               |
| (Opcional) Docker    | ≥ 24               |

---

## Instalação

1. **Clone o repositório**

   ```bash
   git clone https://github.com/seu-usuario/Sentimentos-AI.git
   cd Sentimentos-AI

2. **Crie um ambiente virtual** a partir do `requirements.txt`

   ```bash
   python -m venv .venv              # cria a venv
   # Linux/macOS
   .venv/bin/activate
   # Windows (PowerShell)
   .venv\Scripts\activate

   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   > **Por que usar o `requirements.txt`?**
   > Ele garante que todo mundo trabalhe com as *mesmas* versões de bibliotecas,
   > evitando o clássico “na minha máquina funciona”.

---

## Configurando o `.env`

Crie um arquivo `.env` na raiz com as credenciais do banco (e outras que
preferir). O **`load_dotenv()`** carregará tudo automaticamente na inicialização.

```dotenv
# Banco de dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sentimentos
DB_USER=postgres
DB_PASSWORD=super-segredo

# (Opcional) Token do Evolution API
EVOLUTION_API_TOKEN=EAA...123
```

> **Nunca** faça *commit* do `.env` – ele contém segredos.
> O `.gitignore` já inclui uma regra para protegê-lo.

---

## Criando as tabelas

O serviço assume uma tabela simples chamada **`mensagens`**:

```sql
CREATE TABLE IF NOT EXISTS mensagens (
    id          SERIAL PRIMARY KEY,
    mensagem    TEXT            NOT NULL,
    autor       TEXT,
    data_envio  TIMESTAMPTZ     NOT NULL,
    sentimento  TEXT            -- preenchido pela IA
);
```

Sinta-se à vontade para migrar com Alembic ou gerenciar “na mão” – basta que o
esquema acima exista.

---

## Integrando o Evolution API

### Visão geral

1. **Evolution API** dispara um *webhook* (`Messages Webhook` ou `Messages Set`)
   a cada mensagem recebida/enviada.
2. Um *worker* (por exemplo, **n8n**) consome o webhook e grava a mensagem no
   Postgres.
3. O **Sentimentos-AI** periodicamente busca mensagens cujo campo
   `sentimento IS NULL`, classifica e atualiza a mesma linha.

```
WhatsApp  ──► Evolution API ──► n8n (workflow) ──► Postgres ◄── Sentimentos-AI
```

### Exemplo de workflow n8n

1. **HTTP Webhook (Trigger)**

   * Método: `POST`
   * URL: `/webhook/evolution`
2. **Set / Transform**

   * Normaliza o payload, renomeia campos e **remove o `id`** (para deixar o
     Postgres criar o `SERIAL` automaticamente).
3. **Postgres (Insert)**

   * Tabela: `mensagens`
   * Colunas mapeadas: `mensagem`, `autor`, `data_envio`

> 🔑 **Importante**: Não envie `id = 0`.
> Deixe o banco gerar o próximo valor do *sequence*; isso evita o erro
> `duplicate key value violates unique constraint "mensagens_pkey" (id)=(0)`.

### Observações úteis

| Operação Evolution   | Quando usar                                    |
| -------------------- | ---------------------------------------------- |
| **MESSAGES\_SET**    | Carregar *lotes* históricos pela primeira vez. |
| **MESSAGES\_UPDATE** | Atualizar mensagens já existentes.             |
| **MESSAGES\_UPSERT** | Combinação de insert/update (*idempotente*).   |

---

## Executando a aplicação

```bash
# ainda dentro da venv
python app.py
```

* A API roda em **`http://127.0.0.1:5000`** (ajuste a porta se quiser).
* Um *thread* paralelo (`classify_unlabeled`) faz a classificação a cada
  **120 s** (configurável).

### Com Docker (opcional)

```bash
docker compose up --build
```

> O `docker-compose.yml` (se existir) já traz **Flask + Postgres + pgAdmin**.

---

## Endpoints & métricas

| Rota            | Método | Descrição                                             |
| --------------- | ------ | ----------------------------------------------------- |
| `/mensagens`    | GET    | Todas as mensagens cruas do banco.                    |
| `/metrics`      | GET    | Métricas agregadas *(últimas 24 h / 4 dias / geral)*. |
| `/` (dashboard) | GET    | HTML simples com gráficos gerados em JS.              |

---

## Estrutura do código

```
Sentimentos-AI/
│
├── ai 
│   └── main.py             # ponto de entrada Flask
│   └── tests
├── requirements.txt        # dependências
├── templates/
│   └── dashboard.html      # front-end mínimo
├── README.md               # (você está aqui!)
└── .env.example            # template para o seu .env
```

---

## Próximos passos

* [ ] Adicionar testes unitários (pytest).
* [ ] Melhorar o dashboard com gráficos em tempo real via WebSocket.
* [ ] Expandir o classificador para analisar **emoções** (não só polaridade).

---

## Licença

Distribuído sob a licença **MIT** – veja `LICENSE.md` para detalhes.

```

🔧 **Dúvidas ou sugestões?**  
Abra uma _issue_ ou chame-me no Discord. Bons estudos e bons sentimentos! 🎉
```
