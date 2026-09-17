from bs4 import BeautifulSoup

with open("page_source_modal.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

out = []
for tag in soup.find_all("input"):
    out.append(f"INPUT {tag.attrs}")

# find the modal search input specifically
for tag in soup.find_all(class_=lambda c: c and any("search" in x.lower() or "layer" in x.lower() or "pop" in x.lower() for x in c)):
    out.append(f"{tag.name} {tag.attrs}")

with open("modal_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
