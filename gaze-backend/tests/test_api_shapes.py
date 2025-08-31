"""
Testes para validação de shapes e tratamento de erros da API.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image
import numpy as np

# Cliente de teste
client = TestClient(app)


def create_test_image(width=640, height=480, color=(255, 0, 0)):
    """Cria uma imagem de teste simples."""
    # Criar array numpy com cor especificada
    img_array = np.full((height, width, 3), color, dtype=np.uint8)
    
    # Converter para PIL Image
    img = Image.fromarray(img_array)
    
    # Salvar em buffer de bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    return img_buffer


def test_gaze_endpoint_no_image():
    """Testa /gaze sem imagem para ver erro amigável."""
    response = client.post(
        "/gaze",
        data={"session_id": "test_session"},
        files={}  # Sem arquivo de imagem
    )
    
    assert response.status_code == 422  # Validation Error
    data = response.json()
    assert "detail" in data


def test_gaze_endpoint_invalid_file_type():
    """Testa /gaze com tipo de arquivo inválido."""
    # Criar arquivo de texto em vez de imagem
    text_file = io.BytesIO(b"this is not an image")
    
    response = client.post(
        "/gaze",
        data={"session_id": "test_session"},
        files={"frame": ("test.txt", text_file, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "imagem válida" in data["detail"]


def test_calibrate_endpoint_no_image():
    """Testa /calibrate sem imagem."""
    response = client.post(
        "/calibrate",
        data={"label": "center", "session_id": "test_session"},
        files={}
    )
    
    assert response.status_code == 422  # Validation Error


def test_calibrate_endpoint_invalid_label():
    """Testa /calibrate com label inválido."""
    # Criar imagem de teste
    test_img = create_test_image()
    
    response = client.post(
        "/calibrate",
        data={"label": "invalid_label", "session_id": "test_session"},
        files={"frame": ("test.jpg", test_img, "image/jpeg")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "center" in data["detail"]


def test_calibrate_endpoint_missing_session_id():
    """Testa /calibrate sem session_id."""
    test_img = create_test_image()
    
    response = client.post(
        "/calibrate",
        data={"label": "center"},
        files={"frame": ("test.jpg", test_img, "image/jpeg")}
    )
    
    assert response.status_code == 422  # Validation Error


def test_gaze_endpoint_missing_session_id():
    """Testa /gaze sem session_id."""
    test_img = create_test_image()
    
    response = client.post(
        "/gaze",
        files={"frame": ("test.jpg", test_img, "image/jpeg")}
    )
    
    assert response.status_code == 422  # Validation Error


def test_root_endpoint():
    """Testa endpoint raiz /."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura da resposta
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)


def test_status_endpoint():
    """Testa endpoint /status."""
    response = client.get("/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura da resposta
    assert "status" in data
    assert "websocket_connections" in data
    assert "fps_info" in data
    assert "endpoints" in data
    
    # Verificar tipos
    assert data["status"] == "ok"
    assert isinstance(data["websocket_connections"], int)
    assert isinstance(data["fps_info"], dict)
    assert isinstance(data["endpoints"], dict)


def test_invalid_endpoint():
    """Testa endpoint inexistente."""
    response = client.get("/invalid_endpoint")
    
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])
