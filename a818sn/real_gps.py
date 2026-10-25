# A818SN - REAL GPS using ip-api.com (free, no key)
import json
import urllib.request

def get_real_location():
    try:
        url = "http://ip-api.com/json/"
        with urllib.request.urlopen(url, timeout=8) as r:
            d = json.loads(r.read().decode())
        if d.get("status") == "success":
            return {
                "city": d.get("city", "Unknown"),
                "country": d.get("country", "Unknown"),
                "lat": d.get("lat", 0.0),
                "lon": d.get("lon", 0.0),
                "isp": d.get("isp", "Unknown"),
                "success": True
            }
        return {"success": False, "error": d.get("message", "API failed")}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print(get_real_location())