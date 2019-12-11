class PortRange:
    start: int
    end: int

    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __contains__(self, port: int) -> bool:
        return self.start <= port <= self.end
