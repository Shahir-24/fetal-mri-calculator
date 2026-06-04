from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_index_loads() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Fetal MRI Calculator" in response.text
    assert "Quick case loader" in response.text
    assert "Mild VM" in response.text


def test_calculate_returns_results_partial() -> None:
    response = client.post(
        "/calculate",
        data={
            "gestational_weeks": "24",
            "gestational_days": "0",
            "skull_bpd": "60.32808",
        },
    )
    assert response.status_code == 200
    assert "Structured Report Text" in response.text
    assert "Parent Counseling Note" in response.text
    assert "Assessment Workflow" in response.text
    assert "Retrieved Evidence" in response.text
    assert "Skull biparietal diameter" in response.text
    assert "Expected 5th-95th" in response.text


def test_invalid_measurement_returns_error_message() -> None:
    response = client.post(
        "/calculate",
        data={
            "gestational_weeks": "24",
            "gestational_days": "0",
            "skull_bpd": "abc",
        },
    )
    assert response.status_code == 200
    assert "must be a valid number" in response.text
