from .executable import Executable

class TestCase:

    def __init__(self, executable, options):
        self.options = options
        self.executable = executable

        self.exe = Executable(self.executable)

    def run(self):
        output = self.exe.run(*self.options.args, stdin=self.options.stdin)

        if output.exit_status != options.exit_status:

