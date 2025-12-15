from geopy.geocoders import Nominatim

def get_city_from_coordinates(latitude, longitude):
    try:
        geolocator = Nominatim(user_agent="city_locator")
        location = geolocator.reverse((latitude, longitude), language="fr")

        if location and "address" in location.raw:
            address = location.raw["address"]
            city = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
            return city or "Ville non trouvée"
        else:
            return "Coordonnées invalides ou pas de données disponibles"

    except Exception as e:
        return f"Erreur : {e}"
