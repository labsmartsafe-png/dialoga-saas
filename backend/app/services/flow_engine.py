"""
Motor de execução de fluxos de chatbot.

Responsável por:
- Receber o fluxo e o nó atual
- Devolver a mensagem do bot
- Gerenciar opções, inputs e desvios condicionais
- Manter contexto da conversa
- Detectar fim de fluxo e encaminhar para humano
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models import Flow, Conversation, Message, Lead

# Limite maximo de delay (em segundos) para evitar travamento
MAX_DELAY_SECONDS = 30


# Tipos válidos de nó
VALID_NODE_TYPES = {"message", "question", "input", "condition", "delay", "webhook", "human", "end"}


def _validate_nodes(nodes: List[Dict[str, Any]]) -> List[str]:
    """Valida estrutura básica dos nós. Retorna lista de avisos."""
    warnings = []
    if not nodes:
        warnings.append("Fluxo sem nós.")
        return warnings
    ids_seen = set()
    for n in nodes:
        nid = n.get("id")
        if not nid:
            warnings.append("Nó sem id detectado.")
            continue
        if nid in ids_seen:
            warnings.append(f"id duplicado: {nid}")
        ids_seen.add(nid)
        if n.get("type") not in VALID_NODE_TYPES:
            warnings.append(f"Tipo inválido em {nid}: {n.get('type')}")
    return warnings


def get_node_by_id(nodes: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
    """Busca um nó pelo id."""
    for n in nodes:
        if n.get("id") == node_id:
            return n
    return None


def _render(text: str, context: Dict[str, Any]) -> str:
    """Substitui {{variavel}} no texto pelo valor do contexto."""
    if not text:
        return ""
    try:
        # Substituição simples e segura
        out = text
        for k, v in context.items():
            out = out.replace("{{" + k + "}}", str(v))
        return out
    except Exception:
        return text


def _save_message(
    db: Session,
    conversation_id: int,
    direction: str,
    sender: str,
    content: str,
    node_id: Optional[str] = None,
) -> Message:
    """Salva uma mensagem no histórico."""
    msg = Message(
        conversation_id=conversation_id,
        direction=direction,
        sender=sender,
        content=content,
        node_id=node_id,
        message_type="text",
    )
    db.add(msg)
    return msg


def _ensure_lead(
    db: Session,
    flow: Flow,
    context: Dict[str, Any],
    user_name: Optional[str] = None,
    user_phone: Optional[str] = None,
) -> Lead:
    """Cria um lead a partir do contexto se ainda não existir na conversa."""
    name = context.get("nome") or context.get("name") or user_name
    phone = context.get("telefone") or context.get("phone") or user_phone
    email = context.get("email")
    lead = Lead(
        owner_id=flow.owner_id,
        flow_id=flow.id,
        name=name,
        phone=phone,
        email=email,
        context=context,
        source="simulator",
        status="novo",
    )
    db.add(lead)
    db.flush()
    return lead


def start_conversation(
    db: Session,
    flow: Flow,
    user_name: Optional[str] = "Visitante",
    user_phone: Optional[str] = None,
) -> Conversation:
    """Inicia uma nova conversa para o fluxo, indo até o primeiro nó executável."""
    if not flow.nodes:
        raise ValueError("Fluxo sem nós definidos.")

    start_id = flow.start_node_id or (flow.nodes[0].get("id") if flow.nodes else None)
    if not start_id:
        raise ValueError("Fluxo sem nó inicial definido.")

    conv = Conversation(
        flow_id=flow.id,
        channel="simulator",
        state={"current_node": start_id, "context": {}},
        is_active=True,
    )
    # snapshot do usuário
    if user_phone:
        conv.user_phone = user_phone
    if user_name:
        conv.state["context"]["nome"] = user_name
    db.add(conv)
    db.flush()

    # Executa nós iniciais encadeados que não exigem input (mensagens, delays)
    _run_until_blocking(db, conv, flow)
    db.commit()
    db.refresh(conv)
    return conv


def _run_until_blocking(db: Session, conv: Conversation, flow: Flow) -> None:
    """
    Executa automaticamente os nós que não exigem resposta do usuário
    (message, delay, condition) até encontrar um nó que aguarda resposta.
    """
    nodes = flow.nodes or []
    current_id = (conv.state or {}).get("current_node")
    safety = 0
    while current_id and safety < 100:
        safety += 1
        node = get_node_by_id(nodes, current_id)
        if not node:
            break
        ntype = node.get("type")

        if ntype == "message":
            text = _render(node.get("content", ""), conv.state.get("context", {}))
            _save_message(db, conv.id, "outbound", "bot", text, current_id)
            # BUGFIX: nao usar 'or current_id' pois causa loop infinito
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "delay":
            # BUGFIX: agora o delay espera de verdade!
            segundos = node.get("delay_seconds", 1) or 1
            try:
                segundos = int(segundos)
            except (ValueError, TypeError):
                segundos = 1
            # Limita ao maximo permitido
            segundos = min(segundos, MAX_DELAY_SECONDS)
            # Salva uma mensagem de sistema informando o delay
            _save_message(
                db, conv.id, "outbound", "system",
                f"[Aguardando {segundos}s...]", current_id
            )
            db.commit()  # Persiste a mensagem imediatamente
            # Renova a sessao para evitar expiracao durante sleep longo
            db.expire_all()
            time.sleep(segundos)
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "condition":
            # Avalia condition básica e segue o ramo correspondente
            nxt = _eval_condition(node, conv.state.get("context", {}))
            current_id = nxt or node.get("next") or node.get("fallback")
            conv.state["current_node"] = current_id

        elif ntype == "webhook":
            # Apenas simulação - registra no log
            _save_message(
                db, conv.id, "outbound", "system",
                f"[WEBHOOK acionado] {node.get('content','')}", current_id
            )
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "human":
            _save_message(
                db, conv.id, "outbound", "system",
                "Encaminhado para atendimento humano.",
                current_id,
            )
            conv.is_active = False
            conv.ended_at = datetime.now(timezone.utc)
            _ensure_lead(db, flow, conv.state.get("context", {}))
            return

        elif ntype == "end":
            _save_message(
                db, conv.id, "outbound", "system",
                "Conversa encerrada. Obrigado!",
                current_id,
            )
            # Cria/atualiza lead final
            _ensure_lead(db, flow, conv.state.get("context", {}))
            conv.is_active = False
            conv.ended_at = datetime.now(timezone.utc)
            return

        elif ntype in ("question", "input"):
            # Bloqueante - mostra mensagem (se houver) e espera resposta
            text = _render(node.get("content", ""), conv.state.get("context", {}))
            if text:
                _save_message(db, conv.id, "outbound", "bot", text, current_id)
            return

        else:
            _save_message(
                db, conv.id, "outbound", "system",
                f"[Nó desconhecido: {ntype}]", current_id,
            )
            return


def _eval_condition(node: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
    """
    Avalia uma condição simples:
    {"variable": "cidade", "equals": "São Paulo", "next": "node_id"}
    Retorna o 'next' se verdadeiro.
    """
    cond = node.get("condition") or {}
    var = cond.get("variable")
    val = context.get(var) if var else None
    if "equals" in cond and str(val) == str(cond["equals"]):
        return cond.get("next")
    if "contains" in cond and cond["contains"] in str(val):
        return cond.get("next")
    return None


def send_user_message(
    db: Session,
    conversation: Conversation,
    flow: Flow,
    text: Optional[str] = None,
    selected_option: Optional[str] = None,
) -> Conversation:
    """Processa uma resposta do usuário e avança o fluxo."""
    nodes = flow.nodes or []
    current_id = (conversation.state or {}).get("current_node")
    node = get_node_by_id(nodes, current_id) if current_id else None

    if not node:
        # Conversa sem nó atual - finaliza
        conversation.is_active = False
        conversation.ended_at = datetime.now(timezone.utc)
        _ensure_lead(db, flow, (conversation.state or {}).get("context", {}))
        db.commit()
        return conversation

    context = conversation.state.setdefault("context", {})

    # Salva mensagem do usuário
    user_content = text or selected_option or ""
    _save_message(
        db, conversation.id, "inbound", "user", user_content, current_id
    )

    # Captura variável se for input/question
    variable = node.get("variable")
    if variable and text is not None:
        context[variable] = text

    # Define próximo nó
    next_id = None
    if node.get("type") == "question" and selected_option is not None:
        # Procura opção correspondente
        options = node.get("options") or []
        matched_opt = None
        for opt in options:
            if (
                str(opt.get("value")) == str(selected_option)
                or str(opt.get("label")) == str(selected_option)
            ):
                matched_opt = opt
                break
        if matched_opt:
            # Se a opção tem variável própria, salva nela
            if matched_opt.get("variable"):
                context[matched_opt["variable"]] = (
                    matched_opt.get("value") or matched_opt.get("label")
                )
            # Senão, e se o nó tem variável, salva o value/label selecionado
            elif node.get("variable"):
                context[node["variable"]] = (
                    matched_opt.get("value") or matched_opt.get("label")
                )
            next_id = matched_opt.get("next") or node.get("next")
        else:
            next_id = node.get("next")
    else:
        next_id = node.get("next")

    if not next_id:
        # Sem próximo - finaliza
        conversation.state["current_node"] = None
        conversation.is_active = False
        conversation.ended_at = datetime.now(timezone.utc)
        _ensure_lead(db, flow, context)
    else:
        conversation.state["current_node"] = next_id
        # Executa próximos nós automáticos
        _run_until_blocking(db, conversation, flow)
        # Se ficou inativo durante _run_until_blocking, garante lead criado
        if not conversation.is_active:
            # Verifica se já existe lead desta conversa
            from ..models import Lead as LeadModel
            existing = db.query(LeadModel).filter(LeadModel.flow_id == flow.id).filter(
                LeadModel.context == conversation.state.get("context", {})
            ).first()
            if not existing:
                _ensure_lead(db, flow, context)

    db.commit()
    db.refresh(conversation)
    return conversation


def serialize_conversation(db: Session, conv: Conversation) -> Dict[str, Any]:
    """Converte uma conversa em dict para a API."""
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return {
        "conversation_id": conv.id,
        "finished": conv.is_active is False,
        "context": (conv.state or {}).get("context", {}),
        "messages": [
            {
                "id": m.id,
                "direction": m.direction,
                "sender": m.sender,
                "content": m.content,
                "node_id": m.node_id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ],
    }


def get_current_node_view(db: Session, conv: Conversation, flow: Flow) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, str]]]]:
    """Retorna o nó atual e opções (se houver) para exibição no simulador."""
    current_id = (conv.state or {}).get("current_node")
    if not current_id:
        return None, None
    node = get_node_by_id(flow.nodes or [], current_id)
    if not node:
        return None, None
    opts = None
    if node.get("type") == "question":
        opts = node.get("options") or []
    return node, opts
