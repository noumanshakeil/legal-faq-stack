import pytest

@pytest.mark.asyncio
async def test_faq_ask(client):
    await client.post(
        "/api/faq",
        json={
            "jurisdiction": "US",
            "category": "privacy",
            "question": "Do we need a DPA for processors?",
            "answer": "Under typical US SaaS practice, a DPA is used when a vendor processes personal data on your behalf.",
        },
    )
    r = await client.post(
        "/api/ask", json={"question": "Do SaaS vendors need a DPA?", "jurisdiction": "US"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["citations"]
    assert "legal advice" in body["disclaimer"].lower()
