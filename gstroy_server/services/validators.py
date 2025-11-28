import ipaddress


def validate_ip(ip: str) -> str:
    try:
        ipaddress.IPv4Address(ip)
        return ip
    except ValueError:
        raise ValueError(f"????????? IP ?????: {ip}")
