# RFC — Banco Universitário

|  |  |
| --- | --- |
| **Time** | Equipe Bootcamp |
| **Data** | 12/10/2026 |
| **Versão** | 8 |

## Contextualização

### Entendendo o problema

O projeto consiste em um banco digital para estudantes universitários. O sistema oferece operações de gestão de contas correntes e poupança, transferências, divisão de despesas, resgate de benefícios e contratação de seguros. O modelo permite múltiplas contas por cliente; não há uma operação específica de subconta.

É necessário garantir a segurança do dinheiro sob concorrência. A solução deve ser capaz de lidar com requisições simultâneas, retentativas de rede, possíveis transações duplicadas ou divergência de valores no extrato. Fica fora do escopo desta entrega integrações com open finance, operações de crédito e investimentos.

### Explicando a solução de forma macro

A solução utiliza uma arquitetura limpa em camadas:

* **Validação de Entrada:** Os dados entram protegidos por schemas, rejeitando valores inválidos na camada de *Resources*.
* **Segurança Transacional:** A lógica do negócio reside nos *Controllers*, que gerenciam sessões unificadas via contexto de requisição.
* **Como garantir integridade:** Transferências exigem uma `idempotency_key` com restrição `UNIQUE` mapeada diretamente no banco de dados. Tentativas de duplicidade disparam `IntegrityError` tratadas como conflito (`409`).
* **Como controlar a concorrência:** Transferências bloqueiam as contas envolvidas com `FOR UPDATE`, ordenadas pelo ID da conta. Essa ordem reduz o risco de *deadlock* entre transferências que seguem o mesmo fluxo; não é uma garantia geral contra *deadlocks* em qualquer operação futura.
* `Soft delete` — não implementada: a API atual não oferece exclusão de clientes, contas ou transações. A exclusão física pode comprometer referências e auditoria; *soft delete*, por si só, preserva os registros.
* `N Tabelas para N tipos de contas` — descartada porque multiplicaria a complexidade das consultas de extrato e aumentaria a chance de *deadlocks*. O modelo com tabela de tipos (`account_type`) permite esta flexibilidade.
* `Paginação via Offset no extrato` — o método de controller existente usa cursor pelo ID crescente da transação. O cursor permite continuar a consulta após o último ID retornado; não representa um snapshot imutável diante de novas inserções.

## Implementação

### Rotas e Contratos

> **Nota:**
> As rotas `GET /` e `GET /health_check` são públicas. As demais rotas registradas exigem `INTERNAL-TOKEN`; sem ele ou com valor incorreto, a resposta é `403 Forbidden`.
> Erros de domínio usam o envelope `{title, description, translation, code}`.

| Método | Caminho | O que faz | Entrada | Saídas |
| --- | --- | --- | --- | --- |
| `GET` | `/` | Identifica o serviço. | Aberta, sem token. | `200` com `service` e `id` do processo. |
| `GET` | `/health_check` | Verifica a saúde do serviço. | Aberta, sem token. | `204 No Content`. |
| `POST` | `/customers` | Cadastra o estudante após validar o formato e a matemática do CPF e consultar o vínculo acadêmico. | `INTERNAL-TOKEN`, `document` (11 dígitos), `university_id`, `course_id` | `201` com `customer_key`; `400 QIT000001` schema inválido; `403 QIT000002` token ausente/inválido; `409 QIT001410` CPF duplicado; `422 QIT001424` CPF inválido ou `QIT001425` vínculo inválido; `502 QIT001502` falha na API universitária; `504 QIT001504` timeout. |
| `POST` | `/accounts` | Abre uma conta corrente ou poupança para um cliente. | `INTERNAL-TOKEN`, `customer_key` (UUID), `type_id` (inteiro >= 1) | `201` com `account_key`; `400 QIT000001` payload inválido; `403 QIT000002` token inválido; `404 QIT001101` cliente inexistente; `500 QIT001500` status inicial não configurado. |
| `POST` | `/transactions` | Realiza uma transferência financeira em centavos. | `INTERNAL-TOKEN`, `idempotency_key` (mínimo 5 caracteres), `origin_account_key`, `destination_account_key` (UUIDs), `amount` (inteiro >= 1) | `201` com `transaction_key`; `400 QIT000001` schema inválido ou `QIT001429` origem e destino iguais; `403 QIT000002` token inválido; `404 QIT001102` conta de origem ou destino inexistente; `409 QIT001412` chave de idempotência duplicada; `422 QIT001427` saldo insuficiente. |
| `GET` | `/accounts/{account_key}/transactions` | Consulta débitos e créditos de uma conta, paginados por cursor. | `INTERNAL-TOKEN`, `account_key` (UUID), `limit` (opcional, padrão 10, de 1 a 100), `cursor` (opcional, ID positivo da última transação) | `200` com `data` e `next_cursor`; `400 QIT000010` UUID ou parâmetro inválido; `403 QIT000002` token inválido; `404 QIT001102` conta inexistente. |
| `GET` | `/benefits` | Lista o catálogo de benefícios e parceiros com seus alvos de elegibilidade. | `INTERNAL-TOKEN` | `200` com `data` (lista, vazia quando não há benefícios); `403 QIT000002` token inválido. |
| `POST` | `/benefits/{key}/redemptions` | Resgata um benefício sujeito à elegibilidade de curso e universidade. | `INTERNAL-TOKEN`, `customer_key` (UUID) | `201` com `voucher_code`; `400 QIT000001` payload inválido; `403 QIT000002` token inválido; `404 QIT001101` cliente ou `QIT001103` benefício inexistente; `409 QIT001409` benefício já resgatado; `422 QIT001422` universidade ou `QIT001423` curso inelegível. |
| `POST` | `/insurances` | Contrata um seguro para o cliente. | `INTERNAL-TOKEN`, `customer_key` (UUID), `insurance_id` (inteiro >= 1) | `201` com `policy_number` (UUID); `400 QIT000001` payload inválido; `403 QIT000002` token inválido; `404 QIT001101` cliente ou `QIT001104` seguro inexistente; `409 QIT001411` seguro já contratado. |
| `POST` | `/transactions/{transaction_key}/splits` | Registra a divisão do valor de uma transação entre contas pagadoras. | `INTERNAL-TOKEN`, `splits` (array não vazio de objetos `{account_key, amount}`; UUID e inteiro >= 1) | `201` divisão registrada; `400 QIT000001` schema inválido ou `QIT001400` conta pagadora duplicada; `403 QIT000002` token inválido; `404 QIT001105` transação inexistente; `422 QIT001428` soma diferente do total ou `QIT001426` conta pagadora inexistente. |

### Banco de Dados (Diagrama ER)

## Principal desafio arquitetural
> * **Qual é:** Preservar a consistência dos saldos e a rastreabilidade das operações financeiras sob concorrência.
> * **Por que é difícil:** Retentativas de rede ou execuções simultâneas podem gerarobreposição e negativando a conta de forma indevida.
> * **Como o desenho implementado ajuda:** A tabela `account` possui `CHECK (balance >= 0)`, `transaction.idempotency_key` é `UNIQUE`, e a transferência bloqueia as contas com `FOR UPDATE` em ordem crescente de ID. A regra de saldo no controller compara o saldo de origem com o valor da transferência. Essas medidas protegem o saldo e evitam repetição da chave; não há constraint ou trigger que impeça alterações/exclusões diretas no histórico de transações.

### Diagrama

```mermaid
erDiagram
    UNIVERSITY ||--o{ CUSTOMER : "estuda em"
    COURSE ||--o{ CUSTOMER : "cursa"
    UNIVERSITY ||--o{ BENEFIT : "restringe a"
    COURSE ||--o{ BENEFIT : "restringe a"
    
    ACCOUNT_TYPE ||--o{ ACCOUNT : "define"
    ACCOUNT_STATUS ||--o{ ACCOUNT : "esta em"
    
    CUSTOMER ||--o{ ACCOUNT : "possui"
    CUSTOMER ||--o{ BENEFIT_REDEMPTION : "resgata"
    CUSTOMER ||--o{ CONTRACTED_INSURANCE : "contrata"
    
    ACCOUNT ||--o{ TRANSACTION : "origina"
    ACCOUNT ||--o{ TRANSACTION : "recebe"
    ACCOUNT ||--o{ ACCOUNT_STATUS_EVENT : "sofre"
    ACCOUNT_STATUS ||--o{ ACCOUNT_STATUS_EVENT : "registra"
    
    TRANSACTION ||--o{ SPLIT_BILL : "dividida em"
    ACCOUNT ||--o{ SPLIT_BILL : "paga por"
    
    PARTNER ||--o{ BENEFIT : "oferece"
    BENEFIT ||--o{ BENEFIT_REDEMPTION : "e resgatado em"
    INSURANCE ||--o{ CONTRACTED_INSURANCE : "possui contrato"

    UNIVERSITY {
        serial id PK
        varchar name "Ex: USP, UNICAMP"
    }

    COURSE {
        serial id PK
        varchar name "Ex: Engenharia, Direito"
    }

    CUSTOMER {
        serial id PK "interno"
        uuid customer_key UK "externo"
        varchar document UK "CPF (11 digitos)"
        int university_id FK 
        int course_id FK 
        timestamp created_at
    }

    INSURANCE {
        serial id PK
        varchar name "Nome do seguro"
        int monthly_premium "Valor em centavos"
    }

    CONTRACTED_INSURANCE {
        serial id PK
        uuid policy_number UK "Apólice"
        int insurance_id FK
        int customer_id FK
        timestamp created_at
    }

    ACCOUNT_TYPE {
        serial id PK
        varchar name "CHECKING, SAVINGS"
    }

    ACCOUNT_STATUS {
        serial id PK
        varchar name "ACTIVE, BLOCKED, CLOSED"
    }

    ACCOUNT {
        serial id PK
        uuid account_key UK 
        int customer_id FK 
        int status_id FK 
        int type_id FK 
        bigint balance "estado em centavos (CHECK >= 0)"
        timestamp created_at
    }

    ACCOUNT_STATUS_EVENT {
        serial id PK
        int account_id FK 
        int from_status_id FK "nulo na criação"
        int to_status_id FK
        timestamp created_at 
    }

    TRANSACTION {
        serial id PK
        uuid transaction_key UK 
        varchar idempotency_key UK 
        int origin_account_id FK 
        int destination_account_id FK 
        bigint amount "em centavos"
        timestamp created_at
    }

    SPLIT_BILL {
        serial id PK 
        int transaction_id FK 
        int payer_account_id FK 
        bigint amount 
        varchar status 
    }

    PARTNER {
        serial id PK
        varchar name 
    }

    BENEFIT {
        serial id PK
        uuid benefit_key UK 
        int partner_id FK 
        int target_university_id FK "nulo = todas"
        int target_course_id FK "nulo = todos"
        varchar title 
    }

    BENEFIT_REDEMPTION {
        serial id PK
        int customer_id FK 
        int benefit_id FK 
        varchar voucher_code
        timestamp created_at 
    }

```

---

### Fluxos

**1. Transação de Transferência**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /transactions {idempotency_key, origem, destino, amount}
    API->>Banco: SELECT contas pelas chaves ORDER BY id ASC FOR UPDATE
    Banco-->>API: contas encontradas e bloqueadas
    API->>API: Confere saldo da origem >= amount
    API->>Banco: UPDATE saldo da origem e do destino
    API->>Banco: INSERT transaction
    API->>Banco: COMMIT
    API-->>Cliente: 201 Created {transaction_key}

    Note over API,Banco: Não há pré-consulta da idempotency_key, validação de status ACTIVE nem tarifa neste fluxo.

```

**2. Retentativa com a mesma chave de idempotência**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: Repete POST /transactions com a mesma chave e saldo suficiente
    API->>Banco: SELECT contas pelas chaves ORDER BY id ASC FOR UPDATE
    Banco-->>API: Contas bloqueadas
    API->>API: Confere saldo e prepara atualização dos saldos
    API->>Banco: INSERT transaction com chave já existente
    Banco-->>API: UNIQUE violation
    API-->>Cliente: 409 QIT001412 TransactionConflictError

    Note over API,Banco: A sessão termina sem COMMIT e desfaz também as atualizações de saldo desta tentativa.
    Note over API,Banco: Se o saldo já for insuficiente, o controller responde 422 QIT001427 antes de tentar o INSERT.

```

**3. Duas transferências disputam o mesmo saldo**

```mermaid
sequenceDiagram
    autonumber
    actor ClienteA
    actor ClienteB
    participant APIA as API A
    participant APIB as API B
    participant Banco as PostgreSQL

    Note over Banco: Saldo inicial da origem 100
    ClienteA->>APIA: Transfere 70 com chave A
    APIA->>Banco: SELECT origem e destino ORDER BY id ASC FOR UPDATE
    Banco-->>APIA: Lock concedido e saldo da origem 100
    ClienteB->>APIB: Transfere 40 com chave B
    APIB->>Banco: SELECT origem e destino ORDER BY id ASC FOR UPDATE
    Note right of APIB: A consulta aguarda o lock da origem
    APIA->>Banco: UPDATE saldos e INSERT transaction
    APIA->>Banco: COMMIT
    APIA-->>ClienteA: 201 Created
    Banco-->>APIB: Lock concedido com saldo atualizado 30
    APIB->>APIB: 30 < 40
    APIB-->>ClienteB: 422 QIT001427 InsufficientBalanceError

    Note over APIB,Banco: B não atualiza saldos nem grava uma transação.

```

**4. Cadastro de Cliente**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL
    participant Ext as UniversityConnector

    Cliente->>API: POST /customers {document, university_id, course_id}
    API->>API: JSON Schema: document com 11 dígitos e IDs inteiros >= 1
    API->>API: Valida os dígitos do CPF

    alt CPF matematicamente inválido
        API-->>Cliente: 422 InvalidDocumentError
    else CPF válido
        API->>Ext: GET /universities/{university_id}/students/{document}
        alt Connector retorna 404
            Ext-->>API: 404 Not Found
            API-->>Cliente: 422 InvalidAcademicBondError
        else Connector retorna 200
            Ext-->>API: 200 OK
            API->>Banco: INSERT customer (...)
            alt Documento já cadastrado
                Banco-->>API: IntegrityError na constraint UNIQUE(document)
                API-->>Cliente: 409 DuplicatedCustomerError
            else Inserção concluída
                API-->>Cliente: 201 Created {customer_key}
            end
        else Outro status externo
            Ext-->>API: status inesperado
            API-->>Cliente: 502 UniversityApiError
        else Timeout
            Ext-->>API: Timeout
            API-->>Cliente: 504 UniversityApiTimeoutError
        end
    end

    Note over API,Banco: A duplicidade é detectada na inserção e não há consulta prévia por CPF

```

**5. Divisão de Conta com sucesso**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /transactions/{key}/splits {splits: [{account_key, amount}]}
    API->>API: Valida estrutura, UUIDs e mínimos do payload
    API->>Banco: SELECT transaction pela chave
    Banco-->>API: Transação encontrada
    API->>API: Confere soma(split.amount) == transaction.amount
    API->>Banco: SELECT contas pelas chaves account_key dos splits
    Banco-->>API: Todas as contas pagadoras encontradas
    API->>Banco: INSERT múltiplos registros em split_bill
    API->>Banco: COMMIT
    API-->>Cliente: 201 Created {status}

    Note over API,Banco: O controller verifica existência das contas, mas não consulta status ACTIVE/BLOCKED/CLOSED.

```

**6. Divisão de Conta — item inválido ou pagador duplicado**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /transactions/{key}/splits com item sem amount
    API->>API: Schema rejeita campo obrigatório ausente
    API-->>Cliente: 400 QIT000001 InvalidSchema

    Cliente->>API: POST /transactions/{key}/splits com account_key duplicado
    API->>API: Controller rejeita pagadores repetidos
    API-->>Cliente: 400 QIT001400 BadRequestError

    Note over API,Banco: Nos dois casos a transação não é consultada e nada é gravado.

```

**7. Divisão de Conta — transação inexistente**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /transactions/{key}/splits com splits válidos
    API->>Banco: SELECT transaction pela chave
    Banco-->>API: Nenhuma linha
    API-->>Cliente: 404 QIT001105 TransactionNotFoundError

    Note over API,Banco: Os valores e as contas pagadoras ainda não são consultados.

```

**8. Divisão de Conta — soma diferente do total**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /transactions/{key}/splits
    API->>Banco: SELECT transaction pela chave
    Banco-->>API: Transação com amount 100
    API->>API: Soma de split.amount resulta em 90
    API-->>Cliente: 422 QIT001428 InvalidSplitAmountError

    Note over API,Banco: As contas pagadoras não são consultadas e nenhum split é gravado.

```

**9. Divisão de Conta — pagador inexistente**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /transactions/{key}/splits com soma correta
    API->>Banco: SELECT transaction pela chave
    Banco-->>API: Transação encontrada
    API->>API: Soma de split.amount == transaction.amount
    API->>Banco: SELECT contas pagadoras pelas account_key dos splits
    Banco-->>API: Uma ou mais contas não encontradas
    API-->>Cliente: 422 QIT001426 InvalidAccountsError

    Note over API,Banco: Nenhum registro de split é gravado.

```

**10. Abertura de Conta**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /accounts {customer_key, type_id}
    API->>Banco: SELECT customer pela customer_key
    alt Cliente inexistente
        Banco-->>API: Nenhuma linha
        API-->>Cliente: 404 CustomerNotFoundError
    else Cliente encontrado
        API->>Banco: SELECT account_status WHERE name = 'ACTIVE'
        alt Status ACTIVE não configurado
            Banco-->>API: Nenhuma linha
            API-->>Cliente: 500 StatusNotConfiguredError
        else Status encontrado
            API->>Banco: INSERT account com status ACTIVE
            API->>Banco: INSERT account_status_event (from_status_id NULL)
            API->>Banco: COMMIT
            API-->>Cliente: 201 Created {account_key}
        end
    end

    Note over API,Banco: A tabela customer não tem status e este fluxo não verifica cliente bloqueado.

```

**11. Autenticação das Rotas**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Auth as Middleware interno
    participant Rota as Resource

    Cliente->>API: Requisição HTTP
    API->>Auth: Verifica path, método e INTERNAL-TOKEN
    alt Path público (/ ou /health_check) ou método OPTIONS
        Auth->>Rota: Encaminha sem exigir token
        Rota-->>Cliente: Resposta da rota pública
    else Token ausente ou inválido
        Auth-->>Cliente: 403 ForbiddenNotInternal
    else Token válido
        Auth->>Rota: Encaminha requisição
        Rota-->>Cliente: Resposta do endpoint
    end

```

**12. Resgate de Benefício**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /benefits/{key}/redemptions {customer_key}
    API->>API: Valida payload e UUID de customer_key
    API->>Banco: SELECT customer pela customer_key
    alt Cliente inexistente
        Banco-->>API: Nenhuma linha
        API-->>Cliente: 404 CustomerNotFoundError
    else Cliente encontrado
        API->>Banco: SELECT benefit pela benefit_key
        alt Benefício inexistente
            Banco-->>API: Nenhuma linha
            API-->>Cliente: 404 BenefitNotFoundError
        else Benefício encontrado
            alt Universidade alvo incompatível
                API-->>Cliente: 422 IneligibleUniversityError
            else Curso alvo incompatível
                API-->>Cliente: 422 IneligibleCourseError
            else Cliente elegível
                API->>Banco: INSERT benefit_redemption
                alt Cliente já resgatou este benefício
                    Banco-->>API: IntegrityError na chave única benefício-cliente
                    API-->>Cliente: 409 BenefitAlreadyRedeemedError
                else Resgate criado
                    API->>Banco: COMMIT
                    API-->>Cliente: 201 Created {voucher_code}
                end
            end
        end
    end

```

**13. Contratação de Seguro**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: POST /insurances {customer_key, insurance_id}
    API->>API: Valida payload, UUID e insurance_id >= 1
    API->>Banco: SELECT customer pela customer_key
    alt Cliente inexistente
        Banco-->>API: Nenhuma linha
        API-->>Cliente: 404 CustomerNotFoundError
    else Cliente encontrado
        API->>Banco: SELECT insurance pelo insurance_id
        alt Seguro inexistente
            Banco-->>API: Nenhuma linha
            API-->>Cliente: 404 InsuranceNotFoundError
        else Seguro encontrado
            API->>Banco: INSERT contracted_insurance
            alt Cliente já contratou este seguro
                Banco-->>API: IntegrityError na chave única seguro-cliente
                API-->>Cliente: 409 InsuranceAlreadyContractedError
            else Contrato criado
                API->>Banco: COMMIT
                API-->>Cliente: 201 Created {policy_number}
            end
        end
    end

```

**14. Consulta de Extrato — paginação por cursor**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: GET /accounts/{account_key}/transactions?limit=10&cursor=...
    API->>API: Valida UUID da conta, limit e cursor
    API->>Banco: SELECT account pela account_key
    alt Conta inexistente
        Banco-->>API: Nenhuma linha
        API-->>Cliente: 404 QIT001102 AccountNotFoundError
    else Conta encontrada
        API->>Banco: SELECT transactions de origem ou destino, id > cursor, ORDER BY id ASC LIMIT limit
        Banco-->>API: Página de transações
        API->>API: Formata cada item como DEBIT ou CREDIT
        API->>API: Define next_cursor pelo ID do último item, ou null se vazio
        API-->>Cliente: 200 {data, next_cursor}
    end

    Note over API,Banco: cursor é o ID interno da transação retornado em next_cursor, não o transaction_key.

```

**15. Listagem do Catálogo de Benefícios**

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as API (FastAPI)
    participant Banco as PostgreSQL

    Cliente->>API: GET /benefits com INTERNAL-TOKEN
    API->>Banco: SELECT benefit JOIN partner ORDER BY benefit.id
    Banco-->>API: Benefícios, parceiros e alvos de elegibilidade
    API-->>Cliente: 200 {data: lista}

    Note over API,Banco: Sem registros, data é uma lista vazia. O endpoint lista o catálogo e não filtra por universidade/curso.

```
