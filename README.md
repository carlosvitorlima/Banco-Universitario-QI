# Banco Universitário

Uma API RESTful desenvolvida em Python e FastAPI para gestão de contas, transações financeiras e resgate de benefícios para universitários, criada para permitir alta simultaneidade, resiliência e integridade de dados.

## Como executar

1. **Clone o repositório:**
```bash
git clone https://github.com/carlosvitorlima/Banco-Universitario-QI.git
```

2. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
```

3. **Suba a infraestrutura via Docker:**
```bash
docker compose up --build -d
```

*A API estará disponível em `http://localhost:3000`.*

## Testes

1. **Execute os testes:**
```bash
docker compose exec api python -m pytest
```