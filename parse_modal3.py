from bs4 import BeautifulSoup

with open("page_source_date.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

out = []
for tag in soup.find_all("button"):
    out.append(f"BUTTON {tag.attrs} | {tag.get_text(strip=True)}")
for tag in soup.find_all("a", class_=lambda c: c and "btn" in " ".join(c)):
    out.append(f"A {tag.attrs} | {tag.get_text(strip=True)}")

with open("modal_out3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
