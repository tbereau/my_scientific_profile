import logging
from time import sleep

from requests import RequestException, Response, get

__all__ = ["ProviderUnavailable", "fetch_json", "fetch_text"]

logger = logging.getLogger(__name__)

# A provider that answers with one of these is healthy and telling us it holds
# no record for the identifier. That is information, not a failure.
ABSENT_STATUS_CODES = frozenset({404, 410})
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
MAX_BACKOFF_SECONDS = 30


class ProviderUnavailable(RuntimeError):
    """An upstream service failed for reasons unrelated to the record itself.

    Callers may degrade the fields this provider would have supplied, but must
    never conclude from this that the work does not exist. A rate limit or a
    504 says nothing about the paper; only `None` does.
    """

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider} unavailable: {message}")


def fetch_json(
    url: str,
    provider: str,
    headers: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> dict | None:
    response = _fetch(url, provider, headers, timeout, retries)
    if response is None:
        return None
    try:
        return response.json()
    except ValueError as error:
        raise ProviderUnavailable(provider, f"{url}: malformed JSON body") from error


def fetch_text(
    url: str,
    provider: str,
    headers: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> str | None:
    response = _fetch(url, provider, headers, timeout, retries)
    return None if response is None else response.text


def _fetch(
    url: str, provider: str, headers: dict | None, timeout: int, retries: int
) -> Response | None:
    """Return a 200 response, None if the record is absent, else raise.

    Retries rate limits and server errors with exponential backoff, honouring
    Retry-After when the provider sends one.
    """
    for attempt in range(retries):
        last_attempt = attempt + 1 == retries
        try:
            response = get(url, headers=headers, timeout=timeout)
        except RequestException as error:
            if last_attempt:
                raise ProviderUnavailable(provider, f"{url}: {error}") from error
            _wait(_backoff(attempt), provider, url, str(error))
            continue
        if response.status_code in ABSENT_STATUS_CODES:
            logger.info(f"{provider} holds no record for {url}")
            return None
        if response.status_code == 200:
            return response
        if response.status_code in RETRY_STATUS_CODES and not last_attempt:
            _wait(
                _retry_after(response, attempt),
                provider,
                url,
                f"HTTP {response.status_code}",
            )
            continue
        raise ProviderUnavailable(provider, f"{url}: HTTP {response.status_code}")
    raise ProviderUnavailable(provider, f"{url}: gave up after {retries} attempts")


def _backoff(attempt: int) -> float:
    return min(2.0**attempt, MAX_BACKOFF_SECONDS)


def _retry_after(response: Response, attempt: int) -> float:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return min(float(header), MAX_BACKOFF_SECONDS)
        except ValueError:
            pass
    return _backoff(attempt)


def _wait(seconds: float, provider: str, url: str, reason: str) -> None:
    logger.info(f"{provider} {reason} for {url}; retrying in {seconds:.0f}s")
    sleep(seconds)
