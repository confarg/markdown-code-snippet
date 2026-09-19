# Guide

## Configuration

<!-- snippet: ../lib/config.yaml -->
```yaml
# The server block is what the quickstart walks through.
server:
  host: localhost
  port: 8080

logging:
  level: INFO
  format: "%(asctime)s %(levelname)s %(message)s"
```

## Renaming a user

<!-- snippet: ../lib/models.py#User.rename -->
```python
def rename(self, name: str) -> User:
    """Return a copy of this user under a new name."""
    return User(name=name, email=self.email, roles=self.roles)
```

## Defaults

<!-- snippet: /lib/settings.py#RETRIES -->
```python
RETRIES = 3
```
