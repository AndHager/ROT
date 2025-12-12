from model import instruction_model

class Program:
    instructions: list[instruction_model.Instruction]
    
    def __init__(self):
        self.instructions = []
        
    def __init__(self, instructions):
        self.instructions = instructions

    def __str__(self) -> str:
        for inst in self.instructions:
            print(inst)
            
        
    