import pytest
from src.validators import validate_email, ValidationError


def test_message():
    with pytest.raises(ValidationError, match="Invalid email address"):
        validate_email("nope")
