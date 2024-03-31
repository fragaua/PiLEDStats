import subprocess # To run commands and fetch os information
from typing import Callable


class PIInfo:

    def __init__(self, name: str, cmd: str, parse_function: Callable[[str], dict], display_format_string="{}"):
        self.bash_cmd = cmd
        self.info_name = name
        self.parse_function = parse_function 
        self.display_string = display_format_string
        
        self.data = None ## Actual data, parsed and saved into the proper format, fetched from shell commands.
        self.info = None ## The information, as a string, ready to display
        self.unparsed_info = None ## The information as fetched directly from the shell command


    def fetch(self) -> str:
        try:
            self.unparsed_info = subprocess.check_output(self.bash_cmd, shell=True).decode("utf-8")
            self.data = self.parse(self.unparsed_info)
            self.info = self.display_string.format(self.data) ## TODO: make this better for stuff with more than 1 data element
            return str(self.info)
        except Exception: ## Unexpected stuff might happen from the parameters <parse_function> or <display_format_string>
            return str("Error displaying {}".format(self.info_name))
    
    def parse(self, unparsed_info: str) -> str:
        return self.parse_function(unparsed_info)