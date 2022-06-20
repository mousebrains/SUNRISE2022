import numpy as np
from matplotlib.cm import ScalarMappable

def generatePHPColourMap(name: str, N: int = 128) -> str:
    cmap = ScalarMappable(cmap=name)
    rgba = cmap.to_rgba(np.linspace(0,1,N),bytes=True)
    array_string = ""
    for row in rgba:
        array_string += f"'#{row[3]:02x}{row[2]:02x}{row[1]:02x}{row[0]:02x}',"
    return array_string[:-1]


if __name__ == "__main__":
    # Salinity
    print("Salinity Colour Map:")
    print(generatePHPColourMap('YlGnBu'))
    print()
    print("Temperature Colour Map:")
    print(generatePHPColourMap('inferno_r'))
