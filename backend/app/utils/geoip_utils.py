import requests

def geoip_lookup(ip_addr):
    """Retourne 'Ville, Pays' ou None en cas d’échec."""
    try:
        if ip_addr.startswith("127.") or ip_addr == "localhost":
            return "Localhost"
        resp = requests.get(f"http://ip-api.com/json/{ip_addr}?fields=status,country,city,query")
        data = resp.json()
        if data.get("status") == "success":
            city = data.get("city")
            country = data.get("country")
            if city and country:
                return f"{city}, {country}"
            elif country:
                return country
        return None
    except Exception as e:
        print(f"GeoIP failed: {e}")
        return None
