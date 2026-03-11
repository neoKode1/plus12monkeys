"""+12 Monkeys SDK client — call the generation API programmatically."""

import json
import logging
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from plus12monkeys.models import GeneratedFile, GeneratedPackage, GenerateResult

logger = logging.getLogger("plus12monkeys")

DEFAULT_BASE_URL = "https://plus12monkeys.com/api/v1"


class Plus12MonkeysError(Exception):
    """Base exception for SDK errors."""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class Client:
    """Client for the +12 Monkeys generation API.

    Usage:
        client = Client()
        result = client.generate_mcp("https://github.com/microsoft/BitNet.git")
        result.write_to("./bitnet-mcp")

        # Or generate an SDK package:
        result = client.generate_sdk("https://github.com/microsoft/BitNet.git")
        result.write_to("./bitnet-sdk")
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialize the client.

        Args:
            base_url: API base URL (default: https://plus12monkeys.com/api/v1).
            api_key: Optional API key for authenticated access.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def generate_mcp(
        self,
        repo_url: str,
        project_name: Optional[str] = None,
    ) -> GenerateResult:
        """Generate an MCP server from a GitHub/HuggingFace repo.

        Args:
            repo_url: Full URL to the repository.
            project_name: Override the auto-generated project name.

        Returns:
            GenerateResult with all generated files.
        """
        return self._generate(repo_url, "mcp", project_name)

    def generate_sdk(
        self,
        repo_url: str,
        project_name: Optional[str] = None,
    ) -> GenerateResult:
        """Generate an SDK package from a GitHub/HuggingFace repo.

        Args:
            repo_url: Full URL to the repository.
            project_name: Override the auto-generated project name.

        Returns:
            GenerateResult with all generated files.
        """
        return self._generate(repo_url, "sdk", project_name)

    def _generate(
        self, repo_url: str, output_type: str, project_name: Optional[str]
    ) -> GenerateResult:
        """Internal: call the /generate endpoint."""
        payload = {"repo_url": repo_url, "output_type": output_type}
        if project_name:
            payload["project_name"] = project_name

        data = self._post("/generate", payload)
        return self._parse_result(data)

    def _post(self, path: str, payload: dict) -> dict:
        """Make a POST request to the API."""
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")

        headers = {"Content-Type": "application/json", "User-Agent": "plus12monkeys-sdk/0.1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            try:
                detail = json.loads(detail).get("detail", detail)
            except (json.JSONDecodeError, AttributeError):
                pass
            raise Plus12MonkeysError(f"API error ({exc.code}): {detail}", exc.code) from exc
        except URLError as exc:
            raise Plus12MonkeysError(f"Connection error: {exc.reason}") from exc

    @staticmethod
    def _parse_result(data: dict) -> GenerateResult:
        """Parse the API response into a GenerateResult."""
        pkg_data = data["package"]
        files = [GeneratedFile(**f) for f in pkg_data.get("files", [])]
        package = GeneratedPackage(
            project_name=pkg_data["project_name"],
            template_id=pkg_data["template_id"],
            framework=pkg_data["framework"],
            deployment=pkg_data["deployment"],
            files=files,
            summary=pkg_data.get("summary", ""),
            setup_instructions=pkg_data.get("setup_instructions", []),
            env_vars=pkg_data.get("env_vars", []),
        )
        return GenerateResult(
            package=package,
            repo_name=data["repo_name"],
            repo_owner=data["repo_owner"],
            repo_description=data["repo_description"],
            primary_language=data["primary_language"],
        )

