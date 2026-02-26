# Back-end Avaliação de Desempenho

Este é um projeto Django para gerenciamento de avaliações de desempenho.

## Configuração

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env` (ou crie um novo).
   - Edite `.env` com suas configurações:
     ```
     DEBUG=True
     SECRET_KEY=sua-secret-key-aqui
     DATABASE_ENGINE=django.db.backends.postgresql
     DATABASE_NAME=nome-do-banco
     DATABASE_USER=usuario
     DATABASE_PASSWORD=senha
     DATABASE_HOST=127.0.0.1
     DATABASE_PORT=5432
     ```

3. Execute as migrações:
   ```
   python manage.py migrate
   ```

4. Execute os testes:
   ```
   python manage.py test core
   ```

5. Inicie o servidor:
   ```
   python manage.py runserver
   ```

## Documentação da API

Acesse `/api/schema/swagger-ui/` para a documentação interativa da API.