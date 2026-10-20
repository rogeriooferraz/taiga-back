from django.http import HttpResponse
from django.test import RequestFactory

from taiga.base.middleware.cors import CorsMiddleware


def test_cors_allows_only_the_configured_frontend_origin():
    middleware = CorsMiddleware(lambda request: HttpResponse("ok"))
    factory = RequestFactory()
    allowed = middleware(factory.get("/api/v1/", HTTP_ORIGIN="http://localhost:9001"))
    assert allowed["Access-Control-Allow-Origin"] == "http://localhost:9001"
    assert allowed["Access-Control-Allow-Credentials"] == "true"
    assert "Origin" in allowed["Vary"]

    denied = middleware(factory.get("/api/v1/", HTTP_ORIGIN="https://evil.example"))
    assert "Access-Control-Allow-Origin" not in denied
    assert "Origin" in denied["Vary"]


def test_cors_preflight_short_circuits_only_for_the_configured_origin():
    called = []
    middleware = CorsMiddleware(lambda request: called.append(True) or HttpResponse("ok"))
    factory = RequestFactory()
    allowed = middleware(factory.options("/api/v1/", HTTP_ORIGIN="http://localhost:9001",
                                          HTTP_ACCESS_CONTROL_REQUEST_METHOD="PATCH"))
    denied = middleware(factory.options("/api/v1/", HTTP_ORIGIN="https://evil.example",
                                         HTTP_ACCESS_CONTROL_REQUEST_METHOD="PATCH"))
    assert allowed.status_code == 204
    assert allowed["Access-Control-Allow-Origin"] == "http://localhost:9001"
    assert denied.status_code == 403
    assert "Access-Control-Allow-Origin" not in denied
    assert not called
