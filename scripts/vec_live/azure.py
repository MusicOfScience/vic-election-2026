"""Read/list-only Azure transport. Provider messages and URLs stay out of logs."""
from datetime import datetime, timezone
import logging
import re
from urllib.parse import parse_qs, urlsplit

from .schema import MAX_ARCHIVE, OPENING, FeedError, identify

AZURE_ACCOUNT = re.compile(r"[a-z0-9]{3,24}")
ENDPOINT = re.compile(r"([a-z0-9]{3,24})\.blob\.core\.windows\.net")


class TransportError(FeedError):
    """A classified Azure access or transport failure."""


def credentials(env, now):
    sas_url = env.get("VEC_SAS_URL")
    if sas_url:
        try:
            url = urlsplit(sas_url)
        except ValueError:
            raise TransportError("Invalid HTTPS Azure results container URL") from None
        if (url.scheme != "https" or not ENDPOINT.fullmatch(url.netloc)
                or url.path not in ("/results", "/results/") or url.fragment):
            raise TransportError("Invalid HTTPS Azure results container URL")
        endpoint = f"https://{url.netloc}"
        sas = url.query
    else:
        account = env.get("VEC_STORAGE_ACCOUNT", "")
        token = env.get("VEC_SAS_TOKEN")
        if not account or not token:
            raise TransportError("Azure credential missing")
        if not AZURE_ACCOUNT.fullmatch(account):
            raise TransportError("Invalid Azure storage account name")
        endpoint = f"https://{account}.blob.core.windows.net"
        sas = token.removeprefix("?")
    fields = parse_qs(sas, keep_blank_values=True)
    if (len(fields.get("sig", [])) != 1 or not fields["sig"][0]
            or any(c.isspace() for c in sas) or "#" in sas):
        raise TransportError("Invalid Azure SAS credential")
    permissions = fields.get("sp", [])
    if (not permissions and "si" not in fields) or (
        permissions and (len(permissions) != 1 or set(permissions[0]) != {"r", "l"})
    ):
        raise TransportError("Azure SAS must carry read and list permissions only")
    if fields.get("sr") not in (None, ["c"]):
        raise TransportError("Azure SAS must be scoped to the results container")
    for field, error in (("st", "Azure SAS is not yet valid"), ("se", "Azure SAS has expired")):
        if field in fields:
            try:
                boundary = datetime.fromisoformat(fields[field][0])
                if len(fields[field]) != 1 or boundary.tzinfo is None:
                    raise ValueError
            except ValueError:
                raise TransportError("Invalid Azure SAS validity period") from None
            if (field == "st" and now < boundary) or (field == "se" and now >= boundary):
                raise TransportError(error)
    return endpoint, sas


def classified(error):
    from azure.core.exceptions import ServiceRequestError, ServiceResponseError

    status = getattr(error, "status_code", None)
    code = getattr(error, "error_code", None)
    if code == "BlobNotFound" or status == 404:
        return TransportError("Azure file or container missing")
    if status in (401, 403) or code in ("AuthenticationFailed", "AuthorizationPermissionMismatch"):
        return TransportError("Azure authentication or permissions rejected")
    if status == 412:
        return TransportError("Azure file changed during download; retry listing")
    if status in (408, 429) or (isinstance(status, int) and status >= 500):
        return TransportError("Azure service unavailable or throttled")
    if isinstance(error, (ServiceRequestError, ServiceResponseError, OSError)):
        return TransportError("Azure network connection failed")
    return TransportError("Azure request failed")


class AzureFeed:
    def __init__(self, env, *, now=None):
        from azure.storage.blob import ContainerClient, ExponentialRetry

        now = now or datetime.now(timezone.utc)
        if now < OPENING:
            raise TransportError("Automated VEC access starts at 18:00 AEDT")
        endpoint, sas = credentials(env, now)
        logger = logging.getLogger("azure")
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        logger.propagate = False
        self.client = ContainerClient(
            endpoint, "results", credential=sas, logging_enable=False, redirect_total=0,
            retry_policy=ExponentialRetry(initial_backoff=1, increment_base=2, retry_total=3,
                                          random_jitter_range=1),
            connection_timeout=7, read_timeout=20, max_single_get_size=4_000_000,
            max_chunk_get_size=4_000_000,
        )

    def available(self):
        from azure.core.exceptions import AzureError

        try:
            for blob in self.client.list_blobs(results_per_page=500):
                if re.search(r"(?:^|/)(?:[^/]*(?:trial|rehearsal|sample|training|test)[^/]*)/", blob.name, re.I):
                    continue
                try:
                    info = identify(blob.name)
                except ValueError:
                    continue
                if (info and not info.sample and
                        (info.reference or datetime.fromisoformat(info.published_at) >= OPENING)):
                    yield blob, info
        except (AzureError, OSError) as error:
            raise classified(error) from None

    def fetch(self, blob):
        from azure.core import MatchConditions
        from azure.core.exceptions import AzureError

        if not blob.etag or blob.size is None or not 0 < blob.size <= MAX_ARCHIVE:
            raise TransportError("Azure file size or identity not acceptable")
        try:
            download = self.client.get_blob_client(blob.name).download_blob(
                etag=blob.etag, match_condition=MatchConditions.IfNotModified, max_concurrency=1)
            buffer = bytearray()
            for chunk in download.chunks():
                buffer.extend(chunk)
                if len(buffer) > blob.size:
                    raise TransportError("Azure download exceeded its listed size")
        except (AzureError, OSError) as error:
            raise classified(error) from None
        if len(buffer) != blob.size:
            raise TransportError("Azure download did not match the listed size")
        return bytes(buffer)
