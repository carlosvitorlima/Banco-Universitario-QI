import re
import uuid
from contextvars import ContextVar


# O nome do cabeçalho que carrega o identificador da requisição.
#
# "X-Request-ID" não é invenção deste projeto: é a convenção que
# balanceadores de carga, proxies e ferramentas de log do mundo inteiro
# já sabem ler. Escolher um nome próprio aqui custaria caro depois, na
# hora de plugar qualquer coisa na frente da API.
REQUEST_ID_HEADER = "X-Request-ID"

# O que aceitamos quando quem chama manda o identificador dele: letras,
# números, hífen e sublinhado, no máximo 64 caracteres. O porquê dessa
# desconfiança está em build_request_id, logo abaixo.
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")

# Quando não há requisição nenhuma acontecendo — a API subindo, ou o
# aplicação subindo, por exemplo — o log escreve isto no
# lugar do identificador.
NO_REQUEST_ID = "-"


# ────────────────────────────────────────────────────────────────
# Uma variável que sabe em qual requisição ela está
# ────────────────────────────────────────────────────────────────
# O request context fica em utils/, e não em middlewares/, porque o
# logger também precisa dele e não pode importar middlewares/: esse pacote
# importa errors/, que importa utils/logger.py, e fecharia o ciclo. Uma
# ferramenta compartilhada fica em utils/, que não depende das camadas.
#
# ContextVar, em vez de uma variável comum, mantém um valor separado por
# requisição. Assim, requisições concorrentes não sobrescrevem o
# identificador umas das outras nem precisam passá-lo por todas as camadas.
_request_id: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST_ID)


def get_request_id() -> str:
    """Devolve o identificador da requisição que está sendo atendida agora."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Guarda o identificador desta requisição. Quem chama é o middleware."""
    _request_id.set(request_id)


def build_request_id(received_request_id: str = None) -> str:
    """Aproveita o identificador que veio de fora, ou inventa um novo.

    Aproveitar o que veio é o que permite seguir um mesmo pedido
    atravessando vários sistemas: se o serviço A chamou esta API
    mandando o identificador dele, os dois logs contam a mesma história
    com o mesmo nome.

    Mas o valor veio de FORA, e é por isso que ele passa por uma peneira
    antes. Cabeçalho é texto que qualquer pessoa escreve, e este vai
    parar no log — quem mandasse uma quebra de linha no meio escreveria
    uma linha de log inteira, inventada, dentro do seu arquivo de log.
    Isso tem nome: log injection. Quem manda algo fora do formato
    simplesmente não é atendido no capricho: ganha um identificador novo.

    Repare no `fullmatch`, e não `match`: o `match` se contenta com um
    começo certo e deixa passar o lixo que vier depois.
    """
    if received_request_id is not None and SAFE_REQUEST_ID.fullmatch(received_request_id):
        return received_request_id

    return str(uuid.uuid4())
