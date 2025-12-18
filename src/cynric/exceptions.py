class UnvalidatedDatasetError(Exception):
    def __init__(self, message: str = "An UnvalidatedDatasetError has occurred"):
        super().__init__(message)
        self.message = message


class EmptyDatasetError(Exception):
    def __init__(self, message: str = "An EmptyDatasetError has occurred"):
        super().__init__(message)
        self.message = message


class NoDictionaryError(Exception):
    def __init__(self, message: str = "A NoDictionaryError has occurred"):
        super().__init__(message)
        self.message = message


class InvalidUrlError(Exception):
    def __init__(self, message: str = "A InvalidUrlError has occurred"):
        super().__init__(message)
        self.message = message


class InvalidTokenError(Exception):
    def __init__(self, message: str = "A InvalidTokenError has occurred"):
        super().__init__(message)
        self.message = message


class ExpiredTokenError(InvalidTokenError):
    def __init__(self, message: str = "A ExpiredTokenError has occurred"):
        super().__init__(message)
        self.message = message


class CredentialNotSaved(Exception):
    def __init__(self, message: str = "A SecretNotSaved has occurred"):
        super().__init__(message)
        self.message = message
