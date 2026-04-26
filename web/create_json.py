import time
import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from playwright.sync_api import sync_playwright

default_url = "https://dinosaurking.fandom.com/wiki"
csv_files = [
    "fire",
    "water",
    "grass",
    "lightning",
    "earth",
    #    "secret",
    "move",
    # "char",
    "wind",
]
output_json = "./public/assets/new_dino.json"


def download_site_with_playwright(request_url: str) -> str:
    with sync_playwright() as p:
        # Browser starten (headless=True bedeutet im Hintergrund)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        try:
            # Gehe zur Seite
            page.goto(request_url, wait_until="networkidle")
            # Falls Cloudflare eine Sekunde braucht:
            time.sleep(2)
            # Den fertigen HTML Inhalt extrahieren
            html = page.content()
            browser.close()
            return html
        except Exception as e:
            print(f"Fehler beim Laden von {request_url}: {e}")
            browser.close()
            return ""


def create_request_url(suffix: str) -> str:
    return f"{default_url}/{suffix}"


def download_site(request_url: str) -> bytes:
    return requests.get(request_url).content


def convert_site_to_bs_object(site: bytes) -> BeautifulSoup:
    return BeautifulSoup(site, "html.parser")


def get_stats(bs):
    stats = dict()
    sign = [
        li.get_text(strip=True)
        for li in bs.find_all("li")
        if li.find("a", title="Sign")
    ]

    cleaned_sign_lst = [s.replace("Sign: ", "") for s in sign]
    stats["sign"] = cleaned_sign_lst

    strength = [
        li.get_text(strip=True)
        for li in bs.find_all("li")
        if li.find("a", title="Strength")
    ]

    cleaned_lst = [s.replace("Strength: ", "") for s in strength]
    stats["strength"] = cleaned_lst
    tech = [
        li.get_text(strip=True)
        for li in bs.find_all("li")
        if li.find("a", title="Technique")
    ]
    cleaned_lst = [s.replace("Technique: ", "") for s in tech]
    stats["tech"] = cleaned_lst
    h2_attack = bs.find("a", title="Attack")
    if h2_attack != None:
        try:
            ul = h2_attack.find_next("ul")
            expected_keys = ["Paper", "Rock", "Scissors"]

            values = {key: None for key in expected_keys}

            for li in ul.find_all("li"):
                key, value = li.text.rsplit(": ", 1)  # Trenne Name vom Wert
                key = key.split(" (")[0].strip()
                for subkey in key.split("/"):
                    subkey = subkey.strip()
                    if subkey in values:
                        # Speichert den Wert als Integer
                        values[subkey] = int(value.strip())

            # 4️⃣ Endgültiges Dictionary erstellen
            attack_data = {"attack": values}
            stats["attack"] = values
        except:
            pass
    return stats


def get_type(bs):
    h2 = bs.find("a", title="Types")
    if h2 != None:
        ul = h2.find_next("ul")
        types = list()

        for li in ul.find_all("li"):
            matches = re.findall(r"([\w-]+) Type", li.text)
            types.extend(matches)
        return types


def get_usage(bs):
    filtered_items = [
        li.text.replace("Usage Condition: ", "")
        for li in bs.find_all("li")
        if li.text.startswith("Usage Condition:")
    ]
    return filtered_items


def parse_compatibility(comp_string):
    """
    Wandelt Strings wie 'Compatibility Tabs: 1-3 (okay), 4-6 (great)'
    oder 'Compatibility: Tab 1' in ein strukturiertes Dictionary um.
    """
    if comp_string is None or not str(comp_string).strip():
        return None

    result = {
        "preference": [],  # Für Dinos (z.B. Tab 1)
        "details": {},  # Für Moves (z.B. great: [4,5,6])
    }

    # 1. Suche nach Tab-Präferenzen (Dinos) - "Tab 1" oder "Tab 1, 2"
    tab_matches = re.findall(r"Tab\s*(\d+)", comp_string, re.IGNORECASE)
    if tab_matches:
        result["preference"] = [int(t) for t in tab_matches]

    # 2. Suche nach Bereichen mit Status (Moves) - "1-3 (okay)"
    # Pattern: Bereich (Zahl-Zahl oder Zahl) gefolgt von (status)
    range_pattern = r"(\d+)(?:-(\d+))?\s*\((.*?)\)"
    ranges = re.findall(range_pattern, comp_string)

    for start, end, status in ranges:
        status = status.lower().strip()
        start = int(start)
        end = int(end) if end else start

        # Erzeuge eine Liste der Tabs für diesen Status
        tab_list = list(range(start, end + 1))

        if status in result["details"]:
            result["details"][status].extend(tab_list)
        else:
            result["details"][status] = tab_list

    # Clean up: Falls "details" leer ist (Dino-Case), lösche den Key
    if not result["details"]:
        del result["details"]
    # Falls "preference" leer ist (Move-Case), lösche den Key
    if not result["preference"]:
        del result["preference"]

    return result


def get_compat_tabs(bs):
    results = []
    for li in bs.find_all("li"):
        text = li.get_text(strip=True).replace("\xa0", " ")
        if "Compatibility" in text:
            print(f"✅ Gefunden: {text}")
            value = text.split(":", 1)[1].strip()
            results.append(value)
    return results


def get_effect(bs):
    filtered_items = [
        li.text.replace("Effect: ", "")
        for li in bs.find_all("li")
        if li.text.startswith("Effect:")
    ]

    return filtered_items


def remove_newlines(obj):
    if isinstance(obj, dict):
        return {k: remove_newlines(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [remove_newlines(item) for item in obj]
    elif isinstance(obj, str):
        return obj.replace("\n", "")
    else:
        return obj


def get_card_image(bs, alt_attribute):
    posib = ["card", "Card", ""]
    for p in posib:
        header = bs.find(id="Arcade_Stats")
        if header is not None:
            img = header.find_next("img")
        # img = bs.find("img", attrs={'alt': f'{alt_attribute} {p}'})
        try:
            print(img.get("src"))
            print(img.get("data-src"))
        except:
            img = None
        if img is not None:
            return img.get("data-src")


def create_dino(csv_file) -> list:
    dino_json_data = list()
    # CSV-Datei einlesen
    with open(f"./csv/{csv_file}.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)  # Erste Zeile als Header nehmen
        csv_data = [row for row in reader]

    # JSON aktualisieren
    for row in csv_data:
        name = row[1].strip()
        skill_type = row[2].strip()
        site = download_site_with_playwright(create_request_url(name))
        bs_object = convert_site_to_bs_object(site)
        compat_tab = get_compat_tabs(bs_object)
        stats = get_stats(bs_object)
        usage = get_usage(bs_object)
        effect = get_effect(bs_object)
        card_code = row[4].strip()
        compat = row[3].strip()
        #    img = get_card_image(bs_object, name)
        dino = dict()
        dino["name"] = remove_newlines(name)
        dino["type"] = remove_newlines(skill_type)
        dino["stats"] = remove_newlines(stats)
        dino["sign"] = csv_file
        dino["card_type"] = "dino"
        if csv_file == "move" or csv_file == "secret":
            dino["stats"]["strength"] = list()
            dino["card_type"] = "move"
        dino["usage"] = remove_newlines(usage)
        dino["effect"] = remove_newlines(effect)
        dino["card_code"] = card_code
        # dino["img_url"] = img
        dino["compat_tab"] = parse_compatibility(
            compat_tab[0] if compat_tab else None)
        dino["compat"] = compat
        dino["system"] = "dino_king"
        dino_json_data.append(dino)

        fix_tech(dino)
    return dino_json_data


def fix_tech(dino: dict):
    new_tech = []
    compat = None
    for entry in dino["stats"]["tech"]:
        match = re.match(r"(\d+)(?:\s*Compatibility:\s*(.*))?", entry)
        if match:
            new_tech.append(match.group(1))  # Die Zahl extrahieren
            if match.group(2):  # Falls "Compatibility: ..." existiert
                compatibility = match.group(2)

    dino["stats"]["tech"] = new_tech  # Tech-Liste mit nur Zahlen speichern
    if compat:
        dino["stats"]["compatibility"] = compatibility  # Neuen Key hinzufügen


def save_dinos_to_json(dino_data: list):
    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(dino_data, file, indent=4, ensure_ascii=False)


def download_image(url, index):
    filename = f"./cards_img/{index}.webp"
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    print(f"File downloaded successfully: {filename}")
        else:
            print(f"Failed to download file. Status code: {
                  response.status_code}")

    except Exception:
        print(f"could not load {url}, {Exception}")
        filename = "./cards_img/default.webp"
    return filename


def clean_data(dino_data: list):
    def condition(x):
        return x["name"] == "Card"

    print([x for x in dino_data if not condition(x)])
    return [x for x in dino_data if not condition(x)]


if __name__ == "__main__":
    data = list()
    for csv_name in csv_files:
        data.extend(create_dino(f"{csv_name}"))
        print(f"{csv_name} is finished")
    # for index, d in enumerate(data):
    # d["id"] = index
    # d["img_url"] = download_image(d["img_url"], index)
    data = clean_data(data)
    save_dinos_to_json(data)
