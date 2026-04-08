"""+12 Monkeys SDK — programmatic MCP server and SDK package generation.

Usage:
    from plus12monkeys import Client

    client = Client(api_key="p12m_...")
    result = client.generate_mcp("https://github.com/microsoft/BitNet.git")
    result.write_to("./output")

    # Or use env var: export PLUS12MONKEYS_API_KEY=p12m_...
    import os
    client = Client(api_key=os.environ["PLUS12MONKEYS_API_KEY"])
"""

from plus12monkeys.client import Client
from plus12monkeys.models import GeneratedFile, GeneratedPackage, GenerateResult

__version__ = "0.1.0"
__all__ = ["Client", "GeneratedFile", "GeneratedPackage", "GenerateResult"]

