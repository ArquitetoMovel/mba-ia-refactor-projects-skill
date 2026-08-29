"""Integration tests for core API behavior after MVC refactor."""

from __future__ import annotations


def auth_header(client, email="admin@loja.com", senha="admin123"):
    response = client.post("/login", json={"email": email, "senha": senha})
    token = response.get_json()["dados"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_does_not_leak_secrets(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "secret_key" not in data
    assert "debug" not in data
    assert "db_path" not in data
    assert data["ambiente"] == "teste"


def test_login_with_seed_user(client):
    response = client.post(
        "/login",
        json={"email": "joao@email.com", "senha": "123456"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["sucesso"] is True
    assert body["dados"]["email"] == "joao@email.com"
    assert "senha" not in body["dados"]
    assert body["dados"]["token"]


def test_usuarios_do_not_return_password(client):
    response = client.get("/usuarios", headers=auth_header(client))
    assert response.status_code == 200
    for usuario in response.get_json()["dados"]:
        assert "senha" not in usuario


def test_sensitive_routes_require_authentication(client):
    assert client.get("/usuarios").status_code == 401
    assert client.get("/pedidos").status_code == 401
    assert client.post("/produtos", json={}).status_code == 401


def test_non_admin_cannot_manage_products(client):
    headers = auth_header(client, "joao@email.com", "123456")
    response = client.post(
        "/produtos",
        json={"nome": "Produto", "preco": 10, "estoque": 1},
        headers=headers,
    )
    assert response.status_code == 403


def test_sql_injection_in_produto_id_is_safe(client):
    response = client.get("/produtos/1 OR 1=1")
    assert response.status_code == 404


def test_sql_injection_in_busca_is_safe(client):
    response = client.get("/produtos/busca", query_string={"q": "'; DROP TABLE produtos;--"})
    assert response.status_code == 200
    assert response.get_json()["sucesso"] is True
    # table still works
    assert client.get("/produtos").status_code == 200


def test_criar_pedido_and_list(client):
    produtos = client.get("/produtos").get_json()["dados"]
    produto_id = produtos[0]["id"]

    headers = auth_header(client, "joao@email.com", "123456")
    created = client.post(
        "/pedidos",
        json={"usuario_id": 2, "itens": [{"produto_id": produto_id, "quantidade": 1}]},
        headers=headers,
    )
    assert created.status_code == 201
    pedido_id = created.get_json()["dados"]["pedido_id"]

    listed = client.get("/pedidos/usuario/2", headers=headers)
    assert listed.status_code == 200
    ids = [p["id"] for p in listed.get_json()["dados"]]
    assert pedido_id in ids


def test_admin_query_removed(client):
    response = client.post("/admin/query", json={"sql": "SELECT 1"})
    assert response.status_code == 404


def test_admin_reset_requires_token(client):
    denied = client.post("/admin/reset-db")
    assert denied.status_code == 403

    ok = client.post("/admin/reset-db", headers={"X-Admin-Token": "test-admin-token"})
    assert ok.status_code == 200


def test_duplicate_order_items_are_reserved_atomically(client):
    headers = auth_header(client, "joao@email.com", "123456")
    response = client.post(
        "/pedidos",
        json={
            "usuario_id": 2,
            "itens": [
                {"produto_id": 1, "quantidade": 6},
                {"produto_id": 1, "quantidade": 5},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 400
    product = client.get("/produtos/1").get_json()["dados"]
    assert product["estoque"] == 10


def test_cancel_order_restores_stock(client):
    user_headers = auth_header(client, "joao@email.com", "123456")
    admin_headers = auth_header(client)
    created = client.post(
        "/pedidos",
        json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 2}]},
        headers=user_headers,
    )
    assert created.status_code == 201
    pedido_id = created.get_json()["dados"]["pedido_id"]

    canceled = client.put(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"},
        headers=admin_headers,
    )
    assert canceled.status_code == 200
    assert client.get("/produtos/1").get_json()["dados"]["estoque"] == 10


def test_missing_order_status_update_returns_not_found(client):
    response = client.put(
        "/pedidos/999/status",
        json={"status": "aprovado"},
        headers=auth_header(client),
    )
    assert response.status_code == 404


def test_invalid_product_price_filter_returns_json_error(client):
    response = client.get("/produtos/busca?preco_min=not-a-number")
    assert response.status_code == 400
    assert response.get_json()["sucesso"] is False
