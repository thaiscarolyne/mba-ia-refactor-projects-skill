# Diretrizes de Arquitetura MVC (Model-View-Controller)

Este documento define as regras e responsabilidades recomendadas para estruturação do código em cada camada durante a refatoração para o padrão MVC.

## 1. Estrutura Padrão do Projeto
Todo projeto refatorado deve seguir a seguinte topologia de pastas abaixo de `src/`:
- `src/config/`: Contém segredos, inicialização de conexões e configurações globais alimentadas por arquivos `.env`.
- `src/models/`: Encapsula a lógica de persistência e acesso a dados. Nenhuma rota HTTP ou lógica de apresentação deve tocar a base de dados sem usar a camada de model.
- `src/controllers/`: Responsável por coordenar o fluxo de execução do sistema, recebendo entradas, invocando os modelos de dados e chamando a resposta. Não deve fazer consultas SQL diretas.
- `src/routes/` ou `src/views/`: Mapeia os endpoints HTTP, valida formatos de entrada e direciona para o respectivo controlador. Retorna respostas padronizadas.
- `src/middlewares/`: Centraliza lógica transversal como autenticação/autorização, CORS e interceptores globais de erro.
- `src/app.py` (ou `src/app.js`): Ponto de entrada (Composition Root) que inicializa o framework web e acopla as rotas.

## 2. Responsabilidades das Camadas

### Models
- Gerenciar conexão e queries com o banco de dados.
- Mapear atributos e schemas da tabela para a aplicação.
- Realizar validação de integridade dos dados e regras de negócio puras (ex: se estoque é suficiente).
- **Proibido**: Acessar o request HTTP, cookies, headers ou retornar respostas HTTP (como `jsonify` ou `res.send`).

### Controllers
- Receber os dados processados da requisição.
- Invocar funções dos Models para leitura e escrita no banco.
- Executar lógicas de fluxo de trabalho (como disparar notificações após sucesso).
- **Proibido**: Conter queries SQL brutas ou manipular queries do banco de dados diretamente.

### Views / Routes
- Registrar URIs e métodos HTTP (GET, POST, etc.).
- Extrair parâmetros de URL, query params e corpo da requisição.
- Tratar validações básicas de formato (ex: se campo "email" é obrigatório).
- Retornar as respostas HTTP com os códigos de status adequados (ex: 200, 201, 400, 404, 500).

### Middlewares
- Interceptar a requisição antes de chegar à rota para fazer validações transversais (como checar chaves API, tokens JWT ou sessões).
- Interceptar erros não tratados e formatar em respostas amigáveis.
