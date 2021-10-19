from datetime import timedelta

import pytest
from django.utils import timezone

from ..models import Checkout
from ..tasks import delete_expired_checkouts


def test_delete_expired_checkouts(checkouts_list, customer_user, variant):
    # given
    now = timezone.now()
    checkout_count = Checkout.objects.count()

    expired_anonymous_checkout = checkouts_list[0]
    expired_anonymous_checkout.email = None
    expired_anonymous_checkout.created = now - timedelta(days=40)
    expired_anonymous_checkout.last_change = now - timedelta(days=35)
    expired_anonymous_checkout.lines.create(
        checkout=expired_anonymous_checkout, variant=variant, quantity=1
    )

    not_expired_anonymous_checkout = checkouts_list[1]
    not_expired_anonymous_checkout.email = None
    not_expired_anonymous_checkout.created = now - timedelta(days=35)
    not_expired_anonymous_checkout.last_change = now - timedelta(days=29)
    not_expired_anonymous_checkout.lines.create(
        checkout=not_expired_anonymous_checkout, variant=variant, quantity=1
    )

    expired_user_checkout = checkouts_list[2]
    expired_user_checkout.email = customer_user.email
    expired_user_checkout.created = now - timedelta(days=100)
    expired_user_checkout.last_change = now - timedelta(days=95)
    expired_user_checkout.lines.create(
        checkout=expired_user_checkout, variant=variant, quantity=1
    )

    not_expired_user_empty_checkout = checkouts_list[3]
    not_expired_user_empty_checkout.email = customer_user.email
    not_expired_user_empty_checkout.created = now - timedelta(days=40)
    not_expired_user_empty_checkout.last_change = now - timedelta(hours=2)
    assert not_expired_user_empty_checkout.lines.count() == 0

    empty_checkout = checkouts_list[4]
    empty_checkout.last_change = now - timedelta(hours=8)
    assert empty_checkout.lines.count() == 0

    Checkout.objects.bulk_update(
        [
            expired_anonymous_checkout,
            not_expired_anonymous_checkout,
            expired_user_checkout,
            not_expired_user_empty_checkout,
            empty_checkout,
        ],
        ["created", "last_change", "email"],
    )

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count - 3
    for checkout in [expired_anonymous_checkout, expired_user_checkout, empty_checkout]:
        with pytest.raises(Checkout.DoesNotExist):
            checkout.refresh_from_db()


def test_delete_expired_checkouts_no_checkouts_to_delete(checkout):
    # given
    checkout_count = Checkout.objects.count()

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count
