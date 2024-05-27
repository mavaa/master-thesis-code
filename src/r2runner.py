class R2Runner:
    def __init__(self, subprocess, r2_path="radare2", r2_default_flags="qc"):
        self.subprocess = subprocess
        self.r2_path = r2_path
        self.r2_default_flags = r2_default_flags

    def run(self, command, executable_path, output_path, error=None):
        if error is None:
            error = self.subprocess.DEVNULL

        with open(output_path, 'w') as output_file:
            self.subprocess.run([self.r2_path, f'-{self.r2_default_flags}', command, executable_path],
                                stdout=output_file, stderr=error, check=True)
