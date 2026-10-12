from errors import QIException

class InvalidDocumentNumber(QIException):
    """O CPF tem o formato certo e não existe.

    422, e não 400, de propósito: 400 quer dizer "não consegui ler o seu
    pedido". Aqui a API leu, entendeu, e o valor é que não pode existir —
    os dois últimos dígitos não batem com a conta. A diferença está
    explicada em src/utils/document_number.py.
    """

    code = "QIT001003"

    def __init__(self, document_number) -> None:
        title = "Invalid Document Number"
        http_status = 422
        description = f"The document number {document_number} is not a valid CPF."
        translation = "O CPF informado não é válido."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedDocumentNumber(QIException):
    """Já existe um cadastro com este CPF.

    409 Conflict: o pedido está correto em si, e o que impede é o que já
    está no banco. É a mesma família do SampleEntityFinalStatus aqui em
    cima — conflito com o que já existe, não erro de quem pediu.
    """

    code = "QIT001004"

    def __init__(self, document_number) -> None:
        title = "Document Number already registered"
        http_status = 409
        description = f"There is already an entity with the document number {document_number}."
        translation = "Já existe um cadastro com este CPF."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedEmail(QIException):
    code = "QIT001005"

    def __init__(self, email) -> None:
        title = "Email already registered"
        http_status = 409
        description = f"There is already an entity with the email {email}."
        translation = "Já existe um cadastro com este e-mail."
        super().__init__(title, self.code, http_status, description, translation)

class InvalidBirthdate(QIException):
    """A data tem o formato certo e não existe no calendário.

    Existe porque o `pattern` do schema sabe contar dígitos, não dias:
    "2025-02-30" e "9999-99-99" passam pelo regex e morrem no
    `date.fromisoformat`. Sem esta classe, esse ValueError virava 500 —
    a API culpando a si mesma por um erro de quem chamou.
    """

    code = "QIT001007"

    def __init__(self, birthdate) -> None:
        title = "Invalid Birthdate"
        http_status = 422
        description = f"The birthdate {birthdate} is not a real date."
        translation = "A data de nascimento informada não existe."
        super().__init__(title, self.code, http_status, description, translation)
        
class CustomerNotFoundError(QIException):
    code = "QIT001101"
    def __init__(self):
        super().__init__("Customer Not Found", self.code, 404, "Customer not found.", "Cliente não encontrado.")

class AccountNotFoundError(QIException):
    code = "QIT001102"
    def __init__(self):
        super().__init__("Account Not Found", self.code, 404, "Account not found.", "Conta não encontrada.")

class BenefitNotFoundError(QIException):
    code = "QIT001103"
    def __init__(self):
        super().__init__("Benefit Not Found", self.code, 404, "Benefit not found.", "Benefício não encontrado.")

class InsuranceNotFoundError(QIException):
    code = "QIT001104"
    def __init__(self):
        super().__init__("Insurance Not Found", self.code, 404, "Insurance not found.", "Seguro não encontrado.")

class TransactionNotFoundError(QIException):
    code = "QIT001105"
    def __init__(self):
        super().__init__("Transaction Not Found", self.code, 404, "Transaction not found.", "Transação original não encontrada.")

class StatusNotConfiguredError(QIException):
    code = "QIT001500"
    def __init__(self):
        super().__init__("Status Not Configured", self.code, 500, "Initial status not configured.", "Erro interno: Status inicial não configurado.")

class IneligibleUniversityError(QIException):
    code = "QIT001422"
    def __init__(self):
        super().__init__("Ineligible University", self.code, 422, "Benefit unavailable for this university.", "Benefício indisponível para esta universidade.")

class IneligibleCourseError(QIException):
    code = "QIT001423"
    def __init__(self):
        super().__init__("Ineligible Course", self.code, 422, "Benefit unavailable for this course.", "Benefício indisponível para este curso.")

class InvalidDocumentError(QIException):
    code = "QIT001424"
    def __init__(self, document):
        super().__init__("Invalid Document", self.code, 422, f"Document {document} is mathematically invalid.", "O CPF informado é inválido.")

class InvalidAcademicBondError(QIException):
    code = "QIT001425"
    def __init__(self):
        super().__init__("Invalid Academic Bond", self.code, 422, "Academic bond inactive or not found.", "Vínculo acadêmico não encontrado ou inativo.")

class InvalidAccountsError(QIException):
    code = "QIT001426"
    def __init__(self):
        super().__init__("Invalid Accounts", self.code, 422, "One or more accounts are invalid.", "Uma ou mais contas informadas são inválidas.")

class InsufficientBalanceError(QIException):
    code = "QIT001427"
    def __init__(self):
        super().__init__("Insufficient Balance", self.code, 422, "Account balance is insufficient.", "Saldo insuficiente para a transação.")

class InvalidSplitAmountError(QIException):
    code = "QIT001428"
    def __init__(self, total_split, expected):
        super().__init__("Invalid Split Amount", self.code, 422, "Sum of splits does not match transaction amount.", f"A soma dos valores separados ({total_split}) não bate com a transação total ({expected}).")

class BadRequestError(QIException):
    code = "QIT001400"
    def __init__(self, message):
        super().__init__("Bad Request", self.code, 400, "Bad Request", message)

class SameAccountTransferError(QIException):
    code = "QIT001429"
    def __init__(self):
        super().__init__("Same Account Transfer", self.code, 400, "Origin and destination accounts must be different.", "A conta de origem não pode ser igual à de destino.",)

class BenefitAlreadyRedeemedError(QIException):
    code = "QIT001409"
    def __init__(self):
        super().__init__("Benefit Already Redeemed", self.code, 409, "Customer already redeemed this benefit.", "Você já resgatou este benefício.")

class DuplicatedCustomerError(QIException):
    code = "QIT001410"
    def __init__(self):
        super().__init__("Duplicated Customer", self.code, 409, "Document already exists.", "Já existe um cliente cadastrado com este documento.")

class InsuranceAlreadyContractedError(QIException):
    code = "QIT001411"
    def __init__(self):
        super().__init__("Insurance Already Contracted", self.code, 409, "Customer already has this insurance.", "Você já possui uma apólice ativa para este seguro.")

class TransactionConflictError(QIException):
    code = "QIT001412"
    def __init__(self):
        super().__init__("Transaction Conflict", self.code, 409, "Idempotency key already used.", "Esta transação já foi processada anteriormente.")

class UniversityApiError(QIException):
    code = "QIT001502"
    def __init__(self):
        super().__init__("University API Error", self.code, 502, "Failed to communicate with University API.", "Falha na comunicação com o sistema acadêmico.")

class UniversityApiTimeoutError(QIException):
    code = "QIT001504"
    def __init__(self):
        super().__init__("University API Timeout", self.code, 504, "University API timed out.", "Tempo de resposta esgotado na consulta acadêmica.")