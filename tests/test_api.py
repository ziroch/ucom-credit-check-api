#!/usr/bin/env python3
"""
Script de pruebas para UCOM Credit Check API
=============================================

Ejecuta pruebas automatizadas contra los endpoints de la API
para verificar autenticación, CRUD y verificación de crédito.

Uso:
    python tests/test_api.py

Requiere:
    pip install requests
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
TOKEN = "ucom-secret-token-2026"
HEADERS_VALID = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}
HEADERS_INVALID = {
    "Authorization": "Bearer token-invalido-123",
    "Content-Type": "application/json"
}


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_sin_token():
    """Prueba 1: Acceso sin token debe retornar 401"""
    print_section("PRUEBA 1: Sin token de autenticación")

    response = requests.get(f"{BASE_URL}/companies")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 401, "Debe retornar 401"
    assert "Token no proporcionado" in response.json()["detail"]
    print("PASÓ: Acceso denegado sin token")


def test_token_invalido():
    """Prueba 2: Token inválido debe retornar 401"""
    print_section("PRUEBA 2: Token inválido")

    response = requests.get(f"{BASE_URL}/companies", headers=HEADERS_INVALID)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 401, "Debe retornar 401"
    assert "Token inválido" in response.json()["detail"]
    print("PASÓ: Acceso denegado con token inválido")


def test_crear_empresa():
    """Prueba 3: Crear empresa con token válido"""
    print_section("PRUEBA 3: Crear empresa")

    data = {
        "companyName": "Empresa Test API",
        "streetAddress": "Calle Test 123",
        "city": "Asunción",
        "stateProvince": "Central",
        "postalCode": "1209",
        "country": "Paraguay",
        "phone": "+595991234567",
        "email": "test@empresa.py",
        "status": "ACTIVE"
    }

    response = requests.post(
        f"{BASE_URL}/companies",
        headers=HEADERS_VALID,
        json=data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Debe retornar 200"
    assert "id" in response.json()
    print("PASÓ: Empresa creada exitosamente")
    return response.json()["id"]


def test_listar_empresas():
    """Prueba 4: Listar empresas"""
    print_section("PRUEBA 4: Listar empresas")

    response = requests.get(f"{BASE_URL}/companies", headers=HEADERS_VALID)
    print(f"Status: {response.status_code}")
    print(f"Total empresas: {len(response.json())}")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print("PASÓ: Listado de empresas obtenido")


def test_crear_cuenta(company_id):
    """Prueba 5: Crear cuenta asociada a empresa"""
    print_section("PRUEBA 5: Crear cuenta")

    data = {
        "companyId": company_id,
        "division": "Tecnología",
        "spendingLimit": 5000,
        "discountPercentage": 5,
        "status": "ACTIVE"
    }

    response = requests.post(
        f"{BASE_URL}/accounts",
        headers=HEADERS_VALID,
        json=data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert "id" in response.json()
    print("PASÓ: Cuenta creada exitosamente")


def test_verificar_credito():
    """Prueba 6: Verificar crédito de empresa"""
    print_section("PRUEBA 6: Verificar crédito")

    data = {"companyName": "Empresa Test API"}

    response = requests.post(
        f"{BASE_URL}/credit-check",
        headers=HEADERS_VALID,
        json=data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert 1 <= response.json()["creditScore"] <= 10
    print("PASÓ: Verificación de crédito exitosa")


def test_historial_credito():
    """Prueba 7: Consultar historial de crédito"""
    print_section("PRUEBA 7: Consultar historial")

    response = requests.get(
        f"{BASE_URL}/credit-history/Empresa%20Test%20API",
        headers=HEADERS_VALID
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert len(response.json()) > 0
    print("PASÓ: Historial obtenido exitosamente")


def main():
    print("="*60)
    print("  UCOM CREDIT CHECK API - PRUEBAS AUTOMATIZADAS")
    print("="*60)
    print(f"  URL Base: {BASE_URL}")
    print(f"  Token: {TOKEN}")

    try:
        # Pruebas de seguridad
        test_sin_token()
        test_token_invalido()

        # Pruebas funcionales
        company_id = test_crear_empresa()
        test_listar_empresas()
        test_crear_cuenta(company_id)
        test_verificar_credito()
        test_historial_credito()

        print("\n" + "="*60)
        print("TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("="*60)
        return 0

    except AssertionError as e:
        print(f"\nPRUEBA FALLIDA: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: No se pudo conectar a {BASE_URL}")
        print("   Asegúrate de que la API esté ejecutándose:")
        print("   uvicorn app.main:app --reload --port 8000")
        return 1
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
