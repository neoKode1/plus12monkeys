"""+12 Monkeys SDK — programmatic MCP server and SDK package generation.

Usage:
    from plus12monkeys import Client

    client = Client()  # uses https://plus12monkeys.com by default
    result = client.generate_mcp("https://github.com/microsoft/BitNet.git")
    result.write_to("./output")
"""

from plus12monkeys.client import Client
from plus12monkeys.models import GeneratedFile, GeneratedPackage, GenerateResult

__version__ = "0.1.0"
__all__ = ["Client", "GeneratedFile", "GeneratedPackage", "GenerateResult"]

