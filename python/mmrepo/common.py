"""Common types and utilities."""


__all__ = [
  "GitError",
  "UserError",
]


class UserError(Exception):
  """A user-reportable error."""

  def __init__(self, message: str, *args, **kwargs):
    super().__init__(message.format(*args, **kwargs))

  @property
  def message(self) -> str:
    return self.args[0]


class GitError(Exception):
  """An error from git."""

  def __init__(self, message: str, *args, **kwargs):
    super().__init__(message.format(*args, **kwargs))

  @property
  def message(self) -> str:
    return self.args[0]