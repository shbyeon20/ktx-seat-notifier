from bs4 import BeautifulSoup

with open("page_source.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

print("=== BODY TEXT LENGTH ===")
body = soup.find("body")
print(len(body.get_text(strip=True)) if body else "NO BODY")

print("\n=== INPUTS ===")
for tag in soup.find_all("input"):
    print(tag.attrs)

print("\n=== SELECTS ===")
for tag in soup.find_all("select"):
    print(tag.attrs)

print("\n=== FORMS ===")
for tag in soup.find_all("form"):
    print(tag.attrs)

print("\n=== BUTTONS (first 30) ===")
for tag in soup.find_all("button")[:30]:
    print(tag.attrs, tag.get_text(strip=True)[:30])

print("\n=== DIVs with id (first 40) ===")
for tag in soup.find_all(id=True)[:40]:
    print(tag.name, tag.attrs.get("id"))

print("\n=== IFRAMES ===")
for tag in soup.find_all("iframe"):
    print(tag.attrs)

print("\n=== container div children (direct) ===")
container = soup.find(id="container")
if container:
    for child in container.find_all(recursive=False):
        print(child.name, child.attrs)
else:
    print("no container found")

