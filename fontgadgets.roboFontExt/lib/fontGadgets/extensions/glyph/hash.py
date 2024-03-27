import hashlib
from fontTools.misc.transform import Transform
from fontTools.misc.roundTools import otRound

def getOutlineData(glyph, include_width=True, round=True):
    """
    Generates a string for a given Defcon glyph, considering its contours,
    components, and glyph width. This function will round point coordinates to
    int.

    :param glyph: A Defcon glyph object.
    :param include_width: Boolean to decide if glyph width should be included in the data.
    :param round_points: Boolean to decide if points should be rounded to integers.
    :return: A string representing the glyph data.
    """
    outline_data = []
    round_func = float
    if round:
        round_func = otRound

    for contour in glyph:
        for point in contour:
            outline_data.append(f"{point.segmentType or 'o'},{round_func(point.x)},{round_func(point.y)}")
        outline_data.append("|")

    for component in glyph.components:
        transformation = component.transformation
        tr_string = "".join([f"{t:+}" for t in transformation])
        outline_data.append(f"[{component.baseGlyph}({tr_string})]")

    if include_width:
        outline_data.append(f":{glyph.width}")
    return "".join(outline_data)

def setOutlineData(glyph, data_string):
    """
    Sets the outline data for a given glyph from the given data string.

    :param glyph: A Defcon glyph object.
    :param data_string: A string representing the glyph's outline data.
    """
    if data_string == glyph.getOutlineData():
        # calculating outline data is faster than making it using defcon if data hasn't changed
        return

    glyph.clearContours()
    glyph.clearComponents()

    # Split the data string into components and contour parts
    parts = data_string.split("|")
    for part in parts:
        if part.startswith('[') and part.endswith(']'):
            # Process component
            comp_data = part[1:-1].split('(')
            baseGlyphName, transformation = comp_data[0], comp_data[1]
            tr_values = [float(val) for val in transformation.split(',')]
            transform = Transform(*tr_values)
            glyph.appendComponent(baseGlyphName, transform)
        elif part.startswith(':'):
            # Set glyph width
            glyph.width = int(part[1:])
        elif part:
            # Process contour
            contour = glyph.appendContour()
            point_data = part.split(',')
            for i in range(0, len(point_data), 3):
                segmentType, x, y = point_data[i], float(point_data[i + 1]), float(point_data[i + 2])
                contour.appendPoint((x, y), segmentType if segmentType != 'o' else None)

def outlineHash(glyph, include_width=True):
    """
    Generates a hash for a given Defcon glyph, considering its contours,
    components and glyph width.

    :param glyph: A Defcon glyph object.
    :return: A hash string representing the glyph data.
    """
    data = glyph.getOutlineData(include_width=include_width)
    if len(data) >= 128:
        data = hashlib.sha512(data.encode("ascii")).hexdigest()
    return data
