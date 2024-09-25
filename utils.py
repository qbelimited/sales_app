from flask import request

def get_client_ip():
    """Safely retrieve the client's IP address, accounting for proxies."""
    if request.headers.get('X-Forwarded-For'):
        # Get the first IP in the list (client's IP), which could be comma-separated
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        # Fallback to the direct remote address if no forwarding header is present
        ip = request.remote_addr

    # If no valid IP is found, default to '0.0.0.0'
    return ip or '0.0.0.0'
