"""
Fase D.2.2 — Setup guiado em etapas.

Endpoints separados evitam request pesado:
- criar fluxo
- criar base
- indexar IA
- salvar ROI
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import Flow, ROISettings, User
from ..models_rag import AISettings, KnowledgeBase
from ..services import rag_service, plan_limits


def _node(node_id: str, ntype: str, content: str = "", **extra) -> dict:
    data = {"id": node_id, "type": ntype, "content": content}
    data.update(extra)
    return data


def _input(node_id: str, content: str, variable: str, next_id: str) -> dict:
    return _node(node_id, "input", content, variable=variable, next=next_id)


def _msg(node_id: str, content: str, next_id: Optional[str] = None) -> dict:
    data = _node(node_id, "message", content)
    if next_id:
        data["next"] = next_id
    return data


def _question(node_id: str, content: str, variable: str, options: list[dict]) -> dict:
    return _node(node_id, "question", content, variable=variable, options=options)


PACKAGES: Dict[str, Dict[str, Any]] = {
    "clinica": {
        "title": "Clínica / Odonto",
        "description": "Qualifica interessados e conduz para avaliação/consulta.",
        "pipeline_type": "clinica",
        "appointment_types": ["avaliacao", "consulta"],
        "suggested_tags": ["avaliacao", "procedimento", "urgente", "retorno", "lead_quente"],
        "knowledge_base_seed": """Informações base para clínica/odontologia:\n- Nome da clínica: [preencher]\n- Endereço: [preencher]\n- Horário de atendimento: [preencher]\n- Procedimentos principais: limpeza, clareamento, harmonização, avaliação, implantes, estética facial.\n- Formas de pagamento: Pix, cartão, dinheiro.\n- Política de agendamento: confirmar data e horário com atendente.\n- Caso a IA não saiba responder, encaminhar para atendimento humano.""",
        "flow_name": "Clínica - Triagem e Avaliação",
        "flow_description": "Fluxo pronto para clínicas e odontologia: qualifica o lead e encaminha para agendamento.",
        "nodes": [
            _msg("inicio", "Olá! Seja bem-vindo(a). Vou fazer uma triagem rápida para te direcionar ao melhor atendimento.", "procedimento"),
            _input("procedimento", "Qual procedimento ou atendimento você procura?", "procedimento_interesse", "nome"),
            _input("nome", "Perfeito. Qual é o seu nome?", "nome", "telefone"),
            _input("telefone", "Informe um telefone para contato, por favor.", "telefone", "horario"),
            _input("horario", "Você tem preferência de dia ou horário para uma avaliação/consulta?", "preferencia_horario", "resumo"),
            _msg("resumo", "Obrigado, {{nome}}!\n\nResumo:\nProcedimento: {{procedimento_interesse}}\nTelefone: {{telefone}}\nPreferência: {{preferencia_horario}}\n\nVou encaminhar para um atendente confirmar disponibilidade e valores.", "humano"),
            _node("humano", "human"),
        ],
        "start_node_id": "inicio",
    },
    "petshop": {
        "title": "Petshop",
        "description": "Agenda banho/tosa e organiza dados do pet.",
        "pipeline_type": "petshop",
        "appointment_types": ["banho_tosa", "retorno"],
        "suggested_tags": ["banho_tosa", "vacina", "retorno", "cliente_recorrente", "urgente"],
        "knowledge_base_seed": """Informações base para petshop:\n- Nome do petshop: [preencher]\n- Endereço: [preencher]\n- Horário de atendimento: [preencher]\n- Serviços: banho, tosa, tosa higiênica, hidratação, vacina, consulta parceira.\n- Informe preços aproximados por porte, se desejar.\n- Política: confirmar agenda com atendente antes de concluir.\n- Caso a IA não saiba responder, encaminhar para humano.""",
        "flow_name": "Petshop - Banho e Tosa",
        "flow_description": "Fluxo pronto para petshop: coleta serviço, pet, porte e preferência de horário.",
        "nodes": [
            _msg("inicio", "Olá! Seja bem-vindo(a). Vou te ajudar com o atendimento do seu pet. 🐾", "servico"),
            _question("servico", "Qual serviço você procura?", "servico_pet", [
                {"label": "Banho", "value": "banho", "next": "nome_pet"},
                {"label": "Tosa", "value": "tosa", "next": "nome_pet"},
                {"label": "Banho e tosa", "value": "banho_tosa", "next": "nome_pet"},
                {"label": "Outro", "value": "outro", "next": "nome_pet"},
            ]),
            _input("nome_pet", "Qual é o nome do pet?", "nome_pet", "porte"),
            _input("porte", "Qual é o porte do pet?", "porte_pet", "preferencia"),
            _input("preferencia", "Qual dia/horário você prefere para o atendimento?", "preferencia_horario", "resumo"),
            _msg("resumo", "Obrigado!\n\nResumo:\nServiço: {{servico_pet}}\nPet: {{nome_pet}}\nPorte: {{porte_pet}}\nPreferência: {{preferencia_horario}}\n\nVou encaminhar para confirmar a agenda.", "humano"),
            _node("humano", "human"),
        ],
        "start_node_id": "inicio",
    },
    "veiculos": {
        "title": "Veículos",
        "description": "Qualifica interesse e agenda visita/test-drive.",
        "pipeline_type": "veiculos",
        "appointment_types": ["visita", "test_drive"],
        "suggested_tags": ["test_drive", "financiamento", "troca", "lead_quente", "proposta"],
        "knowledge_base_seed": """Informações base para loja de veículos:\n- Nome da loja: [preencher]\n- Endereço: [preencher]\n- Horário de atendimento: [preencher]\n- Estoque principal: [preencher modelos]\n- Aceita financiamento? [sim/não]\n- Aceita veículo na troca? [sim/não]\n- Condições e documentos necessários: [preencher]\n- Caso a IA não saiba responder, encaminhar para humano.""",
        "flow_name": "Veículos - Interesse e Visita",
        "flow_description": "Fluxo pronto para loja de veículos: qualifica interesse e agenda visita/test-drive.",
        "nodes": [
            _msg("inicio", "Olá! Vou te ajudar a encontrar o veículo ideal e, se fizer sentido, agendar uma visita/test-drive.", "modelo"),
            _input("modelo", "Qual veículo ou modelo você está procurando?", "modelo_interesse", "compra"),
            _input("compra", "Você pretende comprar à vista, financiamento ou ainda está pesquisando?", "forma_compra", "troca"),
            _input("troca", "Você tem veículo para dar na troca?", "tem_troca", "prazo"),
            _input("prazo", "Qual seu prazo para compra ou visita?", "prazo_compra", "resumo"),
            _msg("resumo", "Resumo do interesse:\nVeículo: {{modelo_interesse}}\nForma: {{forma_compra}}\nTroca: {{tem_troca}}\nPrazo: {{prazo_compra}}\n\nVou encaminhar para um consultor verificar disponibilidade e agendar.", "humano"),
            _node("humano", "human"),
        ],
        "start_node_id": "inicio",
    },
    "suporte_tecnico": {
        "title": "Suporte técnico",
        "description": "Triagem de técnico/cliente com chamado, local e dúvida.",
        "pipeline_type": "suporte_tecnico",
        "appointment_types": ["suporte"],
        "suggested_tags": ["chamado", "urgente", "campo", "aguardando_humano", "suporte_n2"],
        "knowledge_base_seed": """Informações base para suporte técnico:\n- Contatos do suporte operacional: [preencher]\n- Horário de atendimento: [preencher]\n- Procedimento para abertura de chamado: [preencher]\n- Dados necessários: número do chamado, local, descrição da dúvida/problema.\n- Casos urgentes: [preencher regra]\n- Caso a IA não saiba responder, encaminhar para humano.""",
        "flow_name": "Suporte Técnico - Triagem de Campo",
        "flow_description": "Fluxo pronto para suporte técnico: valida contato com suporte, coleta chamado, local e dúvida.",
        "nodes": [
            _msg("recepcao", "Olá! Recebemos sua solicitação. Antes de encaminhar o atendimento, vamos fazer uma triagem rápida.", "pergunta_suporte"),
            _question("pergunta_suporte", "Você já fez contato com o setor de Suporte Operacional?", "fez_contato_suporte", [
                {"label": "Sim, já fiz contato", "value": "sim", "next": "pede_chamado"},
                {"label": "Não, ainda não fiz contato", "value": "nao", "next": "contatos_suporte"},
            ]),
            _input("pede_chamado", "Informe o número do chamado.", "numero_chamado", "pede_local"),
            _input("pede_local", "Informe o local do atendimento.", "local_atendimento", "pede_duvida"),
            _input("pede_duvida", "Descreva a dúvida ou dificuldade.", "duvida_tecnica", "resumo"),
            _msg("resumo", "Chamado: {{numero_chamado}}\nLocal: {{local_atendimento}}\nDúvida: {{duvida_tecnica}}\n\nAguarde. Sua solicitação será encaminhada para atendimento humano.", "humano"),
            _node("humano", "human"),
            _msg("contatos_suporte", "Para seguir, faça contato com o Suporte Operacional.\nWhatsApp/Telefone: (XX) XXXXX-XXXX\nE-mail: suporte@suaempresa.com.br", "fim"),
            _node("fim", "end"),
        ],
        "start_node_id": "recepcao",
    },
}


def list_packages() -> List[Dict[str, Any]]:
    return [{"id": k, "title": p["title"], "description": p["description"], "pipeline_type": p["pipeline_type"], "appointment_types": p["appointment_types"], "suggested_tags": p["suggested_tags"]} for k, p in PACKAGES.items()]


def get_package(package_id: str) -> Dict[str, Any]:
    if package_id not in PACKAGES:
        raise KeyError(package_id)
    return PACKAGES[package_id]


def profile_lines(profile: Optional[Dict[str, Any]]) -> str:
    profile = profile or {}
    mapping = [("business_name", "Nome do negócio"), ("address", "Endereço"), ("hours", "Horário"), ("services", "Serviços/produtos"), ("human_contact", "Contato humano"), ("payment_methods", "Pagamento"), ("extra_info", "Extras")]
    lines = []
    for key, label in mapping:
        val = profile.get(key)
        if isinstance(val, str):
            val = val.strip()
        if val:
            lines.append(f"- {label}: {val}")
    return "\n".join(lines)


def customize_seed(package_id: str, profile: Optional[Dict[str, Any]]) -> str:
    seed = get_package(package_id)["knowledge_base_seed"]
    extra = profile_lines(profile)
    return seed + ("\n\nDados informados no setup:\n" + extra if extra else "")


def save_roi_if_present(db: Session, user: User, average_ticket: Optional[float]):
    if average_ticket is None:
        return None
    try:
        ticket = float(average_ticket)
    except Exception:
        return None
    if ticket < 0:
        return None
    settings = db.query(ROISettings).filter(ROISettings.owner_id == user.id).first()
    if settings is None:
        settings = ROISettings(owner_id=user.id, average_ticket=ticket, currency="BRL")
        db.add(settings)
    else:
        settings.average_ticket = ticket
        settings.currency = settings.currency or "BRL"
    db.commit()
    return ticket


def create_flow_from_package(db: Session, user: User, package_id: str, business_name: Optional[str] = None, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    plan_limits.assert_can_create_flow(db, user)
    pkg = get_package(package_id)
    business_name = business_name or (profile or {}).get("business_name")
    name_suffix = f" - {business_name.strip()}" if business_name else ""
    flow = Flow(owner_id=user.id, name=f"{pkg['flow_name']}{name_suffix}", description=pkg["flow_description"], nodes=deepcopy(pkg["nodes"]), start_node_id=pkg["start_node_id"], active=True, template_slug=f"niche:{package_id}", mode="guided")
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return {"ok": True, "package_id": package_id, "flow_id": flow.id, "flow_name": flow.name, "pipeline_type": pkg["pipeline_type"], "appointment_types": pkg["appointment_types"], "suggested_tags": pkg["suggested_tags"], "knowledge_base_seed": customize_seed(package_id, profile)}


def create_kb(db: Session, user: User, package_id: str, business_name: Optional[str], text: str) -> Dict[str, Any]:
    plan_limits.assert_can_create_knowledge_base(db, user)
    pkg = get_package(package_id)
    kb_name = f"Base {pkg['title']}" + (f" - {business_name.strip()}" if business_name else "")
    kb = KnowledgeBase(owner_id=user.id, name=kb_name, description="Criada pelo Setup por Nicho")
    db.add(kb)
    db.commit()
    db.refresh(kb)
    ai = db.query(AISettings).filter(AISettings.owner_id == user.id).first()
    if ai is None:
        ai = AISettings(owner_id=user.id)
        db.add(ai)
    ai.knowledge_base_id = kb.id
    db.commit()
    return {"ok": True, "kb_id": kb.id, "kb_name": kb.name, "text": text}


def index_kb(db: Session, user: User, kb_id: int, text: str) -> Dict[str, Any]:
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id).first()
    if not kb:
        raise KeyError("kb")
    created = rag_service.index_text(db, kb, text, source="setup_nicho")
    return {"ok": True, "kb_id": kb.id, "chunks_created": created}


def apply_package(db: Session, user: User, package_id: str, business_name: Optional[str] = None, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compatibilidade: agora cria só fluxo + texto e salva ROI, sem indexar."""
    profile = profile or {}
    save_roi_if_present(db, user, profile.get("average_ticket"))
    result = create_flow_from_package(db, user, package_id, business_name, profile)
    result["average_ticket_saved"] = profile.get("average_ticket")
    result["next_steps"] = ["Revise o fluxo criado no Builder.", "Crie a base de conhecimento no próximo passo do Setup.", "Ensine a IA em etapa separada.", "Conecte este fluxo na conexão WhatsApp."]
    return result
