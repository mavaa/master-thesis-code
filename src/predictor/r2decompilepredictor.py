class R2DecompilePredictor:
    def __init__(self, r2_runner):
        self.r2_runner = r2_runner
        self.name = "R2_decompile"

    def generate_prediction(self, binary_path, disassembly_path):
        result, error = self.r2_runner.run_str("aaa;pdg", binary_path)

        return result
