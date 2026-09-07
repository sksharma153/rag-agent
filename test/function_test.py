import requests
from bs4 import BeautifulSoup


def decode_secret_message(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    data = []

    for row in soup.find_all("tr")[1:]:
        cols = row.find_all("td")

        if len(cols) != 3:
            continue

        x = int(cols[0].get_text(strip=True))
        char = cols[1].get_text()
        y = int(cols[2].get_text(strip=True))

        data.append((x, y, char))

    if not data:
        return

    max_x = max(x for x, y, char in data)
    max_y = max(y for x, y, char in data)

    # Create grid filled with spaces
    grid = [
        [" " for _ in range(max_x + 1)]
        for _ in range(max_y + 1)
    ]

    # Place characters at their coordinates
    for x, y, char in data:
        grid[y][x] = char

    # y=0 is the bottom, so print from max_y down to 0
    for y in range(max_y, -1, -1):
        print("".join(grid[y]))


url = "https://docs.google.com/document/d/e/2PACX-1vSvM5gDlNvt7npYHhp_XfsJvuntUhq184By5xO_pA4b_gCWeXb6dM6ZxwN8rE6S4ghUsCj2VKR21oEP/pub"

decode_secret_message(url)