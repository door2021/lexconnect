from django.urls import reverse

URL = reverse("network:search")


def names(response):
    return [p.user.handle for p in response.context["results"]]


def test_search_by_name_handle_and_city(client, me, make_lawyer):
    make_lawyer("ayesha_adv", name="Ayesha Siddiqui", city="Lahore")
    make_lawyer("bilal", name="Bilal Ahmed", city="Peshawar")
    assert names(client.get(URL, {"q": "siddiq"})) == ["ayesha_adv"]
    assert names(client.get(URL, {"q": "@bil"})) == ["bilal"]
    assert names(client.get(URL, {"q": "peshawar"})) == ["bilal"]


def test_email_matches_only_exactly_and_is_never_shown(client, me, make_lawyer):
    make_lawyer("ayesha", email="ayesha.s@lawfirm.pk")
    assert names(client.get(URL, {"q": "@lawfirm.pk"})) == []
    assert names(client.get(URL, {"q": "lawfirm"})) == []
    response = client.get(URL, {"q": "Ayesha.S@LawFirm.pk"})
    assert names(response) == ["ayesha"]
    assert "ayesha.s@lawfirm.pk" not in response.content.decode()


def test_search_excludes_self_and_inactive(client, me, make_lawyer):
    gone = make_lawyer("farida")
    gone.user.is_active = False
    gone.user.save()
    assert names(client.get(URL, {"q": "farid"})) == []


def test_empty_query_returns_nothing(client, me, make_lawyer):
    make_lawyer("ayesha")
    assert names(client.get(URL)) == []


def test_query_count_does_not_grow_with_results(
    client, me, make_lawyer, django_assert_max_num_queries
):
    for i in range(20):
        make_lawyer(f"lawyer_{i}", name=f"Lawyer {i}")
    with django_assert_max_num_queries(10):
        response = client.get(URL, {"q": "lawyer"})
    assert len(response.context["results"]) == 20
