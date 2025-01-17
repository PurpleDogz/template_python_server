import requests


def get_ip():
    response = requests.get("https://api64.ipify.org?format=json").json()
    return response["ip"]


def get_ip_location(ip_address):
    response = requests.get(f"https://ipapi.co/{ip_address}/json/")

    if response.status_code == 200:
        json = response.json()
        location_data = {
            "ip": ip_address,
            "city": json.get("city"),
            "region": json.get("region"),
            "country": json.get("country_name"),
        }
        return location_data

    return {}


# print(get_ip_location(get_ip()))
