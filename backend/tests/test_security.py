import pytest
from pydantic import ValidationError

from recal.infrastructure.rate_limit import InMemoryRateLimiter
from recal.interfaces.api_schemas import FeedbackRequest, UserProfileUpdate


def test_rate_limiter_rejects_after_limit() -> None:
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    assert limiter.check("client-1").allowed
    assert limiter.check("client-1").allowed
    decision = limiter.check("client-1")

    assert not decision.allowed
    assert decision.retry_after_seconds > 0


def test_rate_limiter_isolated_by_key() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)

    assert limiter.check("client-1").allowed
    assert not limiter.check("client-1").allowed
    assert limiter.check("client-2").allowed


def test_profile_rejects_empty_interests() -> None:
    with pytest.raises(ValidationError):
        UserProfileUpdate(interests=[])


def test_profile_normalizes_and_deduplicates_values() -> None:
    profile = UserProfileUpdate(
        interests=[" AI ", "AI", "software engineering"],
        countries=[" Benin ", "Benin"],
    )

    assert profile.interests == ["AI", "software engineering"]
    assert profile.countries == ["Benin"]


def test_feedback_comment_is_trimmed_and_bounded() -> None:
    feedback = FeedbackRequest(action="saved", comment="  useful  ")
    assert feedback.comment == "useful"

    with pytest.raises(ValidationError):
        FeedbackRequest(action="saved", comment="x" * 1001)
