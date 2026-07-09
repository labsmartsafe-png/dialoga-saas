"""
Motor de execução de fluxos de chatbot.

Responsável por:
- Receber o fluxo e o nó atual
- Devolver a mensagem do bot
- Gerenciar opções, inputs e desvios condicionais
- Manter contexto da conversa
- Detectar fim de fluxo e encaminhar para humano

FASE A.2:
- Nó 'ai' responde usando RAG.
- Modo 'ai_agent' responde livremente com IA.

FASE CRM 1.0:
- Criação/atualização de Leads centralizada em services/lead_service.py.
- Simulador e WhatsApp passam pela mesma regra de CRM, preservando source.
"""
import time
import unicodedata
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Flow, Conversation, Message, Lead
from ..services import lead_service


MAX_DELAY_SECONDS = 30
VALID_NODE_TYPES = {"message", "question", "input", "condition", "delay", "webhook", "human", "end", "ai"}


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
    for n in nodes:
        if n.get("id") == node_id:
            return n
    return None


def _render(text: str, context: Dict[str, Any]) -> str:
    if not text:
        return ""
    try:
        out = text
        for k, v in context.items():
            out = out.replace("{{" + k + "}}", str(v))
        return out
    except Exception:
        return text


def _normalize_answer(value: Any) -> str:
    """Normaliza resposta para comparar opções digitadas no WhatsApp."""
    if value is None:
        return ""
    txt = str(value).strip().lower()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    cleaned = []
    for ch in txt:
        cleaned.append(ch if ch.isalnum() or ch.isspace() else " ")
    return " ".join("".join(cleaned).split())


def _match_question_option(options: List[Dict[str, Any]], answer: str) -> Optional[Dict[str, Any]]:
    """Encontra opção de +PERG por número, value ou label."""
    raw = str(answer or "").strip()
    norm = _normalize_answer(raw)
    if not norm:
        return None

    if norm.isdigit():
        idx = int(norm) - 1
        if 0 <= idx < len(options):
            return options[idx]

    for opt in options or []:
        for c in (opt.get("value"), opt.get("label")):
            cn = _normalize_answer(c)
            if not cn:
                continue
            if norm == cn or norm.startswith(cn) or cn.startswith(norm):
                return opt
    return None


def _question_text_for_channel(node: Dict[str, Any], context: Dict[str, Any], channel: Optional[str]) -> str:
    """Renderiza +PERG. No WhatsApp, inclui opções numeradas no texto."""
    text = _render(node.get("content", ""), context)
    if channel != "whatsapp":
        return text
    options = node.get("options") or []
    if not options:
        return text
    lines = [text.rstrip(), "", "Responda com o número da opção:"]
    for i, opt in enumerate(options, start=1):
        lines.append(f"{i} - {opt.get('label') or opt.get('value') or ('Opção ' + str(i))}")
    return "\n".join(lines).strip()


def _save_message(
    db: Session,
    conversation_id: int,
    direction: str,
    sender: str,
    content: str,
    node_id: Optional[str] = None,
) -> Message:
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
    """Compatibilidade legada: cria lead de simulador sem conversa.

    Novas conversas devem usar lead_service. Mantido para evitar regressão.
    """
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


def _crm_sync(db: Session, flow: Flow, conv: Conversation, stage: Optional[str] = None, status: Optional[str] = None):
    """Sincroniza lead da conversa com a camada CRM central."""
    lead_service.sync_lead_from_conversation(db, flow, conv, stage=stage, status=status)


def _ai_reply(db: Session, flow: Flow, question: str, node: Optional[Dict[str, Any]] = None) -> str:
    try:
        from ..models_rag import AISettings
        from ..services import rag_service
    except Exception:
        return "Desculpe, a IA não está disponível no momento."

    kb_id = (node or {}).get("knowledge_base_id")
    ai = db.query(AISettings).filter(AISettings.owner_id == flow.owner_id).first()
    if not kb_id and ai is not None:
        kb_id = ai.knowledge_base_id
    if not kb_id:
        return "Ainda não fui treinado com as informações deste negócio. Vou te transferir para um atendente."

    result = rag_service.answer(db, flow.owner_id, kb_id, question)
    if result.get("ok"):
        return result.get("answer") or "..."
    fallback = (ai.fallback_message if ai and ai.fallback_message else "Vou te transferir para um atendente humano.")
    return fallback


def start_conversation(
    db: Session,
    flow: Flow,
    user_name: Optional[str] = "Visitante",
    user_phone: Optional[str] = None,
    channel: str = "simulator",
) -> Conversation:
    """Inicia conversa para o fluxo, indo até o primeiro nó bloqueante."""
    if getattr(flow, "mode", "guided") == "ai_agent":
        conv = Conversation(
            flow_id=flow.id,
            channel=channel,
            state={"current_node": None, "context": {}, "mode": "ai_agent"},
            is_active=True,
        )
        if user_phone:
            conv.user_phone = user_phone
        if user_name:
            conv.state["context"]["nome"] = user_name
        db.add(conv)
        db.flush()
        _crm_sync(db, flow, conv, stage="inicio", status=lead_service.STATUS_EM_ATENDIMENTO)
        saudacao = flow.description or "Olá! Como posso te ajudar hoje? 😊"
        _save_message(db, conv.id, "outbound", "bot", saudacao, None)
        db.commit()
        db.refresh(conv)
        return conv

    if not flow.nodes:
        raise ValueError("Fluxo sem nós definidos.")
    start_id = flow.start_node_id or (flow.nodes[0].get("id") if flow.nodes else None)
    if not start_id:
        raise ValueError("Fluxo sem nó inicial definido.")

    conv = Conversation(
        flow_id=flow.id,
        channel=channel,
        state={"current_node": start_id, "context": {}},
        is_active=True,
    )
    if user_phone:
        conv.user_phone = user_phone
    if user_name:
        conv.state["context"]["nome"] = user_name
    db.add(conv)
    db.flush()
    _crm_sync(db, flow, conv, stage="inicio", status=lead_service.STATUS_EM_ATENDIMENTO)
    _run_until_blocking(db, conv, flow)
    db.commit()
    db.refresh(conv)
    return conv


def _run_until_blocking(db: Session, conv: Conversation, flow: Flow) -> None:
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
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "ai":
            last_user = (
                db.query(Message)
                .filter(Message.conversation_id == conv.id, Message.direction == "inbound")
                .order_by(Message.created_at.desc())
                .first()
            )
            question = (last_user.content if last_user else "") or node.get("content", "") or "Olá"
            resposta = _ai_reply(db, flow, question, node)
            _save_message(db, conv.id, "outbound", "bot", resposta, current_id)
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "delay":
            segundos = node.get("delay_seconds", 1) or 1
            try:
                segundos = int(segundos)
            except (ValueError, TypeError):
                segundos = 1
            segundos = min(segundos, MAX_DELAY_SECONDS)
            _save_message(db, conv.id, "outbound", "system", f"[Aguardando {segundos}s...]", current_id)
            db.commit()
            db.expire_all()
            time.sleep(segundos)
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "condition":
            nxt = _eval_condition(node, conv.state.get("context", {}))
            current_id = nxt or node.get("next") or node.get("fallback")
            conv.state["current_node"] = current_id

        elif ntype == "webhook":
            _save_message(db, conv.id, "outbound", "system", f"[WEBHOOK acionado] {node.get('content','')}", current_id)
            current_id = node.get("next")
            conv.state["current_node"] = current_id

        elif ntype == "human":
            _save_message(db, conv.id, "outbound", "system", "Encaminhado para atendimento humano.", current_id)
            conv.is_active = False
            conv.ended_at = datetime.now(timezone.utc)
            lead_service.mark_handoff(db, flow, conv, stage=current_id or "atendimento_humano")
            return

        elif ntype == "end":
            _save_message(db, conv.id, "outbound", "system", "Conversa encerrada. Obrigado!", current_id)
            conv.is_active = False
            conv.ended_at = datetime.now(timezone.utc)
            lead_service.mark_finished(db, flow, conv, stage=current_id or "fim")
            return

        elif ntype == "question":
            text = _question_text_for_channel(node, conv.state.get("context", {}), getattr(conv, "channel", None))
            if text:
                _save_message(db, conv.id, "outbound", "bot", text, current_id)
            _crm_sync(db, flow, conv, stage=current_id)
            return

        elif ntype == "input":
            text = _render(node.get("content", ""), conv.state.get("context", {}))
            if text:
                _save_message(db, conv.id, "outbound", "bot", text, current_id)
            _crm_sync(db, flow, conv, stage=current_id)
            return

        else:
            _save_message(db, conv.id, "outbound", "system", f"[Nó desconhecido: {ntype}]", current_id)
            return


def _eval_condition(node: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
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
    if getattr(flow, "mode", "guided") == "ai_agent" or (conversation.state or {}).get("mode") == "ai_agent":
        user_content = text or selected_option or ""
        _save_message(db, conversation.id, "inbound", "user", user_content, None)
        resposta = _ai_reply(db, flow, user_content, None)
        _save_message(db, conversation.id, "outbound", "bot", resposta, None)
        _crm_sync(db, flow, conversation, stage="ai_agent", status=lead_service.STATUS_EM_ATENDIMENTO)
        db.commit()
        db.refresh(conversation)
        return conversation

    nodes = flow.nodes or []
    current_id = (conversation.state or {}).get("current_node")
    node = get_node_by_id(nodes, current_id) if current_id else None
    if not node:
        conversation.is_active = False
        conversation.ended_at = datetime.now(timezone.utc)
        lead_service.mark_finished(db, flow, conversation, stage="fim")
        db.commit()
        return conversation

    context = conversation.state.setdefault("context", {})
    user_content = text or selected_option or ""
    _save_message(db, conversation.id, "inbound", "user", user_content, current_id)

    variable = node.get("variable")
    if variable and text is not None:
        context[variable] = text

    next_id = None
    if node.get("type") == "question":
        options = node.get("options") or []
        answer = selected_option if selected_option is not None else text
        matched_opt = _match_question_option(options, answer or user_content)

        if matched_opt:
            chosen_value = matched_opt.get("value") or matched_opt.get("label")
            if matched_opt.get("variable"):
                context[matched_opt["variable"]] = chosen_value
            elif node.get("variable"):
                context[node["variable"]] = chosen_value
            next_id = matched_opt.get("next") or node.get("next")
        else:
            retry = "Não consegui identificar sua opção. Por favor, responda com uma das opções abaixo."
            qtext = _question_text_for_channel(node, context, getattr(conversation, "channel", None))
            _save_message(db, conversation.id, "outbound", "bot", (retry + "\n\n" + qtext).strip(), current_id)
            _crm_sync(db, flow, conversation, stage=current_id, status=lead_service.STATUS_EM_ATENDIMENTO)
            db.commit()
            db.refresh(conversation)
            return conversation
    else:
        next_id = node.get("next")

    _crm_sync(db, flow, conversation, stage=current_id, status=lead_service.STATUS_EM_ATENDIMENTO)

    if not next_id:
        conversation.state["current_node"] = None
        conversation.is_active = False
        conversation.ended_at = datetime.now(timezone.utc)
        lead_service.mark_finished(db, flow, conversation, stage="fim")
    else:
        conversation.state["current_node"] = next_id
        _run_until_blocking(db, conversation, flow)

    db.commit()
    db.refresh(conversation)
    return conversation


def serialize_conversation(db: Session, conv: Conversation) -> Dict[str, Any]:
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
    if getattr(flow, "mode", "guided") == "ai_agent" or (conv.state or {}).get("mode") == "ai_agent":
        return None, None
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
