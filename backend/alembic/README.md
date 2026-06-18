# Migrações do Banco de Dados (Alembic)

> **Nota:** No MVP, o WhatsFlow cria as tabelas automaticamente via `Base.metadata.create_all()` na inicialização (ver `app/database.py` e `app/main.py`). O Alembic está configurado para quando você quiser controlar versionamento de schema.

## Comandos úteis

```bash
# Criar migração após alterar models
cd backend
alembic revision --autogenerate -m "minha mudanca"

# Aplicar migrações
alembic upgrade head

# Reverter
alembic downgrade -1
```

## Para criar a primeira migração (após personalizações)

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
