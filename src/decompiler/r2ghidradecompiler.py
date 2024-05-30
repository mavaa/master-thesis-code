class R2GdhidraDecompiler:
    def __init__(self, r2_runner):
        self.r2_runner = r2_runner

    def decompile(self, executable_path, output_path):
        self.r2_runner.run("aaa;pdg", executable_path, output_path)
