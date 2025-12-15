class AgentInput:
    def __init__(self, inputs: dict):
        self.inputs = inputs

class AgentOutput:
    def __init__(self, output: any):
        self.output = output

class Agent:
    def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError
