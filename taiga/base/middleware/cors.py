# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django import http
from django.conf import settings
from django.utils.cache import patch_vary_headers


CORS_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
CORS_ALLOWED_HEADERS = ["content-type", "x-requested-with",
                        "authorization", "accept-encoding",
                        "x-disable-pagination", "x-lazy-pagination",
                        "x-host", "x-session-id", "set-orders"]
CORS_ALLOWED_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["x-pagination-count", "x-paginated", "x-paginated-by",
                       "x-pagination-current", "x-pagination-next", "x-pagination-prev",
                       "x-site-host", "x-site-register"]

CORS_EXTRA_EXPOSE_HEADERS = getattr(settings, "APP_EXTRA_EXPOSE_HEADERS", [])


class CorsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response is None:
            response = self.get_response(request)
        return self.process_response(request, response)

    def _populate_response(self, request, response):
        origin = request.headers.get("origin")
        front = settings.SITES["front"]
        allowed_origin = f"{front['scheme']}://{front['domain']}"
        patch_vary_headers(response, ["Origin"])
        if origin != allowed_origin:
            return response
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Methods"] = ",".join(CORS_ALLOWED_METHODS)
        response["Access-Control-Allow-Headers"] = ",".join(CORS_ALLOWED_HEADERS)
        response["Access-Control-Expose-Headers"] = ",".join(CORS_EXPOSE_HEADERS + CORS_EXTRA_EXPOSE_HEADERS)
        response["Access-Control-Max-Age"] = "1800"

        if CORS_ALLOWED_CREDENTIALS:
            response["Access-Control-Allow-Credentials"] = "true"
        return response

    def process_request(self, request):
        if "access-control-request-method" in request.headers:
            front = settings.SITES["front"]
            allowed_origin = f"{front['scheme']}://{front['domain']}"
            if request.headers.get("origin") != allowed_origin:
                return http.HttpResponseForbidden()
            return self._populate_response(request, http.HttpResponse(status=204))
        return None

    def process_response(self, request, response):
        return self._populate_response(request, response)
