import ipaddress
import socket
from urllib.parse import urlparse

from rest_framework import serializers
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = "__all__"
        read_only_fields = ["user"]
        extra_kwargs = {
            "secret": {"write_only": True},
        }

    def validate_url(self, value):
        parsed = urlparse(value)

        if parsed.scheme not in ("http", "https"):
            raise serializers.ValidationError("Only http/https URLs are allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise serializers.ValidationError("URL must include a hostname.")

        # Resolve the hostname and reject anything pointing at private,
        # loopback, or link-local ranges — blocks direct SSRF targets like
        # localhost, 169.254.169.254 (cloud metadata), and internal 10.x/192.168.x hosts.
        try:
            resolved_ips = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            raise serializers.ValidationError("Could not resolve hostname.")

        for family, _, _, _, sockaddr in resolved_ips:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise serializers.ValidationError(
                    "Webhook URL resolves to a disallowed internal address."
                )

        return value
