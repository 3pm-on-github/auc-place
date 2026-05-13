import json
from PIL import Image

def convert():
    data = json.load(open("grid.json"))
    height = len(data)
    width = len(data[0])

    img = Image.new("RGB", (width, height))

    pixels = []
    for row in data:
        for hex_color in row:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            pixels.append((r, g, b))

    img.putdata(pixels)
    img.save("grid.png")