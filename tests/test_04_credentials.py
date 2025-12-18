import pytest  # noqa
import support as support  # noqa
import uuid
import keyring

from cynric.credentials.helpers import validate_url, validate_token
from cynric.exceptions import (
    InvalidUrlError,
    InvalidTokenError,
    CredentialNotSaved,
)
from cynric.credentials import credentials
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError


class InMemoryKeyring(KeyringBackend):
    """Simple in-memory keyring backend for tests.

    Stores secrets in a dict keyed by (service, username).
    """

    priority = 1  # not strictly needed since we call set_keyring

    def __init__(self):
        self._data = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        try:
            del self._data[(service, username)]
        except KeyError as e:
            raise PasswordDeleteError("No such password") from e


# Constants
GOOD_URLS = {
    "simple_https": "https://example.com",
    "with_trailing_slash": "https://example.com/",
    "with_path": "https://example.com/api/v1/resource",
    "with_query": "https://example.com/api?foo=bar&baz=1",
    "with_port": "https://example.com:8443/api",
    "with_subdomain": "https://api.sde.wessex.nhs.uk",
    "with_fragment": "https://example.com/path#section1",
    "with_leading_trailing_spaces": "   https://example.com/with/spaces   ",
}

BAD_URLS = {
    # wrong schemes
    "http_scheme": "http://example.com",
    "ftp_scheme": "ftp://example.com/resource",
    "no_scheme": "example.com",
    "relative_path": "/just/a/path",
    # missing netloc
    "https_no_host": "https://",
    "https_only_slash": "https:///path-only",
    "https_space_in_host": "https://exa mple.com/api",
    # spaces in URL
    "space_in_path": "https://example.com/my path",
    "space_in_query": "https://example.com/api?foo=hello world",
    # clearly invalid format
    "just_garbage": "not a url",
    "empty_string": "",
    "only_spaces": "    ",
}

NON_STRING_URLS = [
    None,
    123,
    3.14,
    ["https://example.com"],
    {"url": "https://example.com"},
]

GOOD_TOKEN = (
    "eyJhbGciOiAiSFMyNTYifQ.eyJzdWIiOiAidXNlciIsICJleHAiOiA0MTAyNDQ0ODAwfQ.c2lnbmF0dXJl"
)

BAD_TOKENS = {
    "empty": "",
    "no_dots": "justastring",
    "two_parts": "part1.part2",
    "bad_base64_header": (
        "!!!.eyJzdWIiOiAidXNlciIsICJleHAiOiA0MTAyNDQ0ODAwfQ.c2lnbmF0dXJl"
    ),
    "bad_json_header": (
        "bm90LWpzb24.eyJzdWIiOiAidXNlciIsICJleHAiOiA0MTAyNDQ0ODAwfQ.c2lnbmF0dXJl"
    ),
    "bad_json_payload": "eyJhbGciOiAiSFMyNTYifQ.bm90LWpzb24.c2lnbmF0dXJl",
    "missing_exp": "eyJhbGciOiAiSFMyNTYifQ.eyJzdWIiOiAidXNlciJ9.c2lnbmF0dXJl",
    "exp_not_int": (
        "eyJhbGciOiAiSFMyNTYifQ.eyJzdWIiOiAidXNlciIsICJleHAiOiAibm90YW5pbnQifQ.c2lnbmF0dXJl"
    ),
    "expired": "eyJhbGciOiAiSFMyNTYifQ.eyJzdWIiOiAidXNlciIsICJleHAiOiAxfQ.c2lnbmF0dXJl",
}

TEST_URL_ALIAS = "TEST_BASE_URL"
TEST_URL = "https://example.com"
TEST_TOKEN_ALIAS = "TEST_BASE_URL"
TEST_TOKEN = GOOD_TOKEN


# Helpers
@pytest.fixture
def isolated_keyring(monkeypatch):
    """Install an in-memory keyring and give this test a unique CYNRIC service name."""
    backend = InMemoryKeyring()
    keyring.set_keyring(backend)

    unique_service = f"CYNRIC-{uuid.uuid4()}"
    monkeypatch.setattr(credentials, "CYNRIC", unique_service)

    # Just to be explicit: each test starts with an empty store.
    backend._data.clear()

    return backend


### ====================== ###
### ---------TESTS---------###
### ====================== ###


# Test Validation
@pytest.mark.parametrize("name,url", GOOD_URLS.items())
def test_validate_url_success(name, url):
    result = validate_url(url)
    assert result == url.strip()


@pytest.mark.parametrize("name,url", BAD_URLS.items())
def test_validate_url_invalid(name, url):
    with pytest.raises(InvalidUrlError) as exc_info:
        validate_url(url)
    assert str(exc_info.value) == "Invalid Wessex SDE API URL provided. Please check."


@pytest.mark.parametrize("value", NON_STRING_URLS)
def test_validate_url_non_string(value):
    with pytest.raises(InvalidUrlError):
        validate_url(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "token, expected_message",
    [
        (BAD_TOKENS["empty"], "Token must not be empty"),
        (BAD_TOKENS["no_dots"], "Invalid token format - must have three parts"),
        (BAD_TOKENS["two_parts"], "Invalid token format - must have three parts"),
        (
            BAD_TOKENS["bad_base64_header"],
            "Invalid token. Please contact the Wessex SDE.",
        ),
        (
            BAD_TOKENS["bad_json_header"],
            "Invalid token. Please contact the Wessex SDE.",
        ),
        (
            BAD_TOKENS["bad_json_payload"],
            "Invalid token. Please contact the Wessex SDE.",
        ),
        (BAD_TOKENS["missing_exp"], "Invalid token. Please contact the Wessex SDE."),
        (BAD_TOKENS["exp_not_int"], "Invalid token. Please contact the Wessex SDE."),
        (BAD_TOKENS["expired"], "Token has expired. Please contact the Wessex SDE."),
    ],
)
def test_validate_token_errors(token, expected_message):
    with pytest.raises(InvalidTokenError) as exc_info:
        validate_token(token)
    assert str(exc_info.value) == expected_message


def test_validate_token_success():
    assert validate_token(GOOD_TOKEN) == GOOD_TOKEN


def test_token_must_be_string():
    with pytest.raises(InvalidTokenError):
        validate_token(123)  # type: ignore[arg-type]


# Test Credential Storage
def test_get_missing_raises_secretnotsaved(isolated_keyring):
    # Nothing stored yet
    with pytest.raises(CredentialNotSaved):
        credentials._get(credentials.BASE_URL)


def test_delete_missing_passes(isolated_keyring):
    with pytest.raises(CredentialNotSaved):
        credentials._get(credentials.BASE_URL)

    credentials._delete(credentials.BASE_URL)  # should NOT raise

    # Still missing
    with pytest.raises(CredentialNotSaved):
        credentials._get(credentials.BASE_URL)


def test_save_and_get_credentials_roundtrip(isolated_keyring, monkeypatch):
    base_url_in = TEST_URL
    token_in = TEST_TOKEN

    credentials.save_credentials(base_url_in, token_in)

    url_out = credentials.get_base_url()
    token_out = credentials.get_token()

    assert url_out == base_url_in
    assert token_out == token_in


def test_delete_single_elements(isolated_keyring):
    # Save both, then delete just BASE_URL with _delete.
    credentials._save(credentials.BASE_URL, TEST_URL)
    credentials._save(credentials.TOKEN, TEST_TOKEN)

    credentials._delete(credentials.BASE_URL)

    with pytest.raises(CredentialNotSaved):
        credentials._get(credentials.BASE_URL)

    # Token should still be present
    assert credentials._get(credentials.TOKEN) == TEST_TOKEN


def test_delete_credentials_removes_both(isolated_keyring):
    credentials._save(credentials.BASE_URL, TEST_URL)
    credentials._save(credentials.TOKEN, TEST_TOKEN)

    credentials.delete_credentials()

    with pytest.raises(CredentialNotSaved):
        credentials._get(credentials.BASE_URL)

    with pytest.raises(CredentialNotSaved):
        credentials._get(credentials.TOKEN)


def test_delete_raises_if_backend_fails_and_secret_still_exists(monkeypatch):
    """If the backend raises PasswordDeleteError but the secret is still present,
    _delete should re-raise PasswordDeleteError."""

    class FlakyDeleteKeyring(InMemoryKeyring):
        def delete_password(self, service, username):
            # Pretend delete failed but leave data untouched.
            raise PasswordDeleteError("Simulated failure")

    backend = FlakyDeleteKeyring()
    keyring.set_keyring(backend)

    # Give this test its own CYNRIC namespace
    monkeypatch.setattr(credentials, "CYNRIC", f"CYNRIC-{uuid.uuid4()}")

    # Save a secret
    credentials._save(credentials.BASE_URL, TEST_URL)

    # Because delete_password fails AND the secret still exists,
    # _delete should re-raise PasswordDeleteError.
    with pytest.raises(PasswordDeleteError):
        credentials._delete(credentials.BASE_URL)

    # And the secret should still be retrievable (delete really did fail).
    assert credentials._get(credentials.BASE_URL) == TEST_URL


# Run
if __name__ == "__main__":
    pytest.main([__file__])
