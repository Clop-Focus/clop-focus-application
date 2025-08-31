"""
Módulo para gerenciar calibração de gaze por sessão.
Mantém offsets de calibração em memória volátil.
"""

from typing import Dict, Tuple, Optional
import time

# Armazenamento em memória para offsets de calibração
# session_id -> {"h": offset_h, "v": offset_v, "timestamp": timestamp}
_calibration_store: Dict[str, Dict[str, float]] = {}

# Tempo de expiração para sessões (24 horas)
SESSION_EXPIRY_HOURS = 24


def _cleanup_expired_sessions():
    """Remove sessões expiradas da memória."""
    current_time = time.time()
    expired_sessions = []
    
    for session_id, data in _calibration_store.items():
        if current_time - data.get("timestamp", 0) > SESSION_EXPIRY_HOURS * 3600:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del _calibration_store[session_id]


def get_offsets(session_id: str) -> Tuple[float, float]:
    """
    Obtém offsets de calibração para uma sessão.
    
    Args:
        session_id: ID único da sessão
        
    Returns:
        Tuple (offset_h, offset_v) para os offsets horizontal e vertical
    """
    _cleanup_expired_sessions()
    
    if session_id not in _calibration_store:
        return 0.0, 0.0
    
    data = _calibration_store[session_id]
    return data.get("h", 0.0), data.get("v", 0.0)


def apply_offsets(gaze_dict: Dict, session_id: str) -> Dict:
    """
    Aplica offsets de calibração ao resultado de gaze.
    
    Args:
        gaze_dict: Dicionário com resultado de gaze
        session_id: ID da sessão para aplicar calibração
        
    Returns:
        Dicionário de gaze com offsets aplicados
    """
    if "error" in gaze_dict:
        return gaze_dict
    
    offset_h, offset_v = get_offsets(session_id)
    
    # Aplicar offsets
    gaze_dict["gaze"]["h"] -= offset_h
    gaze_dict["gaze"]["v"] -= offset_v
    
    # Clamp novamente após aplicar offsets
    gaze_dict["gaze"]["h"] = max(-3.0, min(3.0, gaze_dict["gaze"]["h"]))  # Aumentar range para 3.0
    gaze_dict["gaze"]["v"] = max(-3.0, min(3.0, gaze_dict["gaze"]["v"]))
    
    # Recalcular on_screen com valores calibrados (usar thresholds do modelo)
    h = gaze_dict["gaze"]["h"]
    v = gaze_dict["gaze"]["v"]
    attention = gaze_dict["attention"]
    
    # Usar thresholds do modelo se disponível, senão usar padrão
    if "thresholds" in gaze_dict:
        gaze_limit = gaze_dict["thresholds"]["gaze_limit"]
        attention_min = gaze_dict["thresholds"]["attention_min"]
        gaze_dict["on_screen"] = abs(h) <= gaze_limit and abs(v) <= gaze_limit and attention >= attention_min
    else:
        # Fallback para thresholds padrão
        gaze_dict["on_screen"] = abs(h) <= 2.0 and abs(v) <= 2.0 and attention >= 0.05
    
    # Adicionar ou atualizar informações de calibração
    if "calibration" not in gaze_dict:
        gaze_dict["calibration"] = {}
    
    gaze_dict["calibration"]["h"] = offset_h
    gaze_dict["calibration"]["v"] = offset_v
    
    return gaze_dict


def set_calibration(session_id: str, sample_gaze: Dict, label: str) -> Dict[str, float]:
    """
    Define calibração para uma sessão.
    
    Args:
        session_id: ID único da sessão
        sample_gaze: Dicionário com gaze de referência
        label: Tipo de calibração (para V1, apenas "center")
        
    Returns:
        Dicionário com offsets atuais da sessão
    """
    _cleanup_expired_sessions()
    
    if label != "center":
        raise ValueError("Para V1, apenas calibração 'center' é suportada")
    
    if "error" in sample_gaze:
        raise ValueError("Gaze de referência inválido")
    
    # Para calibração "center", assumimos que o usuário está olhando para o centro
    # Os offsets são os valores atuais de gaze (para zerar)
    offset_h = sample_gaze["gaze"]["h"]
    offset_v = sample_gaze["gaze"]["v"]
    
    # Armazenar offsets com timestamp
    _calibration_store[session_id] = {
        "h": offset_h,
        "v": offset_v,
        "timestamp": time.time()
    }
    
    return {"h": offset_h, "v": offset_v}


def get_session_info(session_id: str) -> Optional[Dict]:
    """
    Obtém informações de uma sessão de calibração.
    
    Args:
        session_id: ID da sessão
        
    Returns:
        Dicionário com informações da sessão ou None se não existir
    """
    _cleanup_expired_sessions()
    
    if session_id not in _calibration_store:
        return None
    
    data = _calibration_store[session_id]
    return {
        "h": data.get("h", 0.0),
        "v": data.get("v", 0.0),
        "timestamp": data.get("timestamp", 0),
        "age_hours": (time.time() - data.get("timestamp", 0)) / 3600
    }


def list_active_sessions() -> Dict[str, Dict]:
    """
    Lista todas as sessões ativas de calibração.
    
    Returns:
        Dicionário com informações de todas as sessões ativas
    """
    _cleanup_expired_sessions()
    
    sessions = {}
    for session_id, data in _calibration_store.items():
        sessions[session_id] = {
            "h": data.get("h", 0.0),
            "v": data.get("v", 0.0),
            "timestamp": data.get("timestamp", 0),
            "age_hours": (time.time() - data.get("timestamp", 0)) / 3600
        }
    
    return sessions


def clear_session(session_id: str) -> bool:
    """
    Remove uma sessão de calibração.
    
    Args:
        session_id: ID da sessão para remover
        
    Returns:
        True se a sessão foi removida, False se não existia
    """
    if session_id in _calibration_store:
        del _calibration_store[session_id]
        return True
    return False


def clear_all_sessions():
    """Remove todas as sessões de calibração."""
    _calibration_store.clear()
