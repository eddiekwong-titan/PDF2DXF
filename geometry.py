from math import hypot

def distance(p1, p2):
    return hypot(p2[0]-p1[0], p2[1]-p1[1])


def flip_y(point, page_height):
    return (
        point.x,
        page_height - point.y
    )


def line_length(start, end):
    return hypot(
        end[0]-start[0],
        end[1]-start[1]
    )