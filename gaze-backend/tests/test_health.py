"""
Testes para o endpoint de saúde da aplicação.
"""

import pytest
from fastapi.testclient import TestClient
from app import app

# Cliente de teste
client = TestClient(app)


def test_health_endpoint():
    """Testa se o endpoint /health retorna 200 e status ok."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_response_structure():
    """Testa se a estrutura da resposta do /health está correta."""
    response = client.get("/health")
    data = response.json()
    
    # Verificar se contém apenas a chave "status"
    assert len(data.keys()) == 1
    assert "status" in data
    assert isinstance(data["status"], str)


def test_health_multiple_requests():
    """Testa se o endpoint /health responde consistentemente a múltiplas requisições."""
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__])
