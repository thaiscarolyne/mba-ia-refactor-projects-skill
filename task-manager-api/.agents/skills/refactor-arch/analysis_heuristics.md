# Diretrizes de Análise de Projeto

Este documento fornece heurísticas para detecção automática da stack de tecnologia e arquitetura do projeto analisado.

## Heurísticas de Detecção de Stack

### Linguagem
- **Python**: Presença de arquivos `.py` (ex: `app.py`, `models.py`) e arquivo `requirements.txt` ou `setup.py`.
- **Node.js**: Presença de arquivo `package.json`, pasta `node_modules` ou arquivos `.js` contendo `require()` ou `import`.

### Framework Web
- **Flask**: Arquivos Python contendo `from flask import Flask` ou chamadas `Flask(__name__)`.
- **Express**: Arquivos JavaScript contendo `require('express')` ou `import express`.

### Banco de Dados e Conector
- **SQLite (Nativo Python)**: Importações de `import sqlite3` e chamadas a `sqlite3.connect()`.
- **SQLAlchemy (Python ORM)**: Presença de `flask_sqlalchemy` ou `SQLAlchemy()` no código.
- **sqlite3 (Node.js)**: Importações de `require('sqlite3')`.

## Heurísticas de Mapeamento de Arquitetura

### Monolítica Não Estruturada
- Presença de arquivos aglomerados no diretório raiz (ex: `app.py`, `models.py`, `controllers.py`, `database.py`) onde a lógica de roteamento, negócios e banco de dados está altamente acoplada.
- Arquivos contendo centenas de linhas de código lidando com múltiplos domínios do sistema simultaneamente (ex: uma classe `models.py` que contém funções para produtos, usuários e pedidos sem divisão clara).

### Parcialmente Estruturada
- Presença de pastas como `routes/`, `models/`, `services/`, `utils/`, mas com vazamento de responsabilidades (ex: consultas de banco diretas ou lógica de negócio pesada nos arquivos de rotas, ou uma camada de serviço morta que não é importada em lugar algum).
- Falta de encapsulamento de segredos (configuração hardcoded no ponto de entrada) e falta de middlewares estruturados para segurança ou erros.
