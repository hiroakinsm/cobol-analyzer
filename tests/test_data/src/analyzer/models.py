class ProgramInfo:
    def __init__(self, program_id, is_valid):
        self.program_id = program_id
        self.is_valid = is_valid 

class Program:
    def __init__(self):
        self.has_valid_calls = True

class DependencySummary:
    def __init__(self, programs):
        self.programs = [Program() for _ in range(len(programs))]

class UsageSummary:
    def __init__(self, data_items, total_items):
        self.data_items = data_items
        self.total_items = total_items 