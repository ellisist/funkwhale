import pytest
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone

from funkwhale_api.federation import (
    activity,
    actors,
    models,
    serializers,
    utils,
    views,
    webfinger,
)


@pytest.mark.parametrize(
    "view,permissions",
    [
        (views.LibraryViewSet, ["federation"]),
        (views.LibraryTrackViewSet, ["federation"]),
    ],
)
def test_permissions(assert_user_permission, view, permissions):
    assert_user_permission(view, permissions)


@pytest.mark.parametrize("system_actor", actors.SYSTEM_ACTORS.keys())
def test_instance_actors(system_actor, db, api_client):
    actor = actors.SYSTEM_ACTORS[system_actor].get_actor_instance()
    url = reverse("federation:instance-actors-detail", kwargs={"actor": system_actor})
    response = api_client.get(url)
    serializer = serializers.ActorSerializer(actor)

    if system_actor == "library":
        response.data.pop("url")
    assert response.status_code == 200
    assert response.data == serializer.data


@pytest.mark.parametrize(
    "route,kwargs",
    [
        ("instance-actors-outbox", {"actor": "library"}),
        ("instance-actors-inbox", {"actor": "library"}),
        ("instance-actors-detail", {"actor": "library"}),
        ("well-known-webfinger", {}),
    ],
)
def test_instance_endpoints_405_if_federation_disabled(
    authenticated_actor, db, preferences, api_client, route, kwargs
):
    preferences["federation__enabled"] = False
    url = reverse("federation:{}".format(route), kwargs=kwargs)
    response = api_client.get(url)

    assert response.status_code == 405


def test_wellknown_webfinger_validates_resource(db, api_client, settings, mocker):
    clean = mocker.spy(webfinger, "clean_resource")
    url = reverse("federation:well-known-webfinger")
    response = api_client.get(url, data={"resource": "something"})

    clean.assert_called_once_with("something")
    assert url == "/.well-known/webfinger"
    assert response.status_code == 400
    assert response.data["errors"]["resource"] == ("Missing webfinger resource type")


@pytest.mark.parametrize("system_actor", actors.SYSTEM_ACTORS.keys())
def test_wellknown_webfinger_system(system_actor, db, api_client, settings, mocker):
    actor = actors.SYSTEM_ACTORS[system_actor].get_actor_instance()
    url = reverse("federation:well-known-webfinger")
    response = api_client.get(
        url,
        data={"resource": "acct:{}".format(actor.webfinger_subject)},
        HTTP_ACCEPT="application/jrd+json",
    )
    serializer = serializers.ActorWebfingerSerializer(actor)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/jrd+json"
    assert response.data == serializer.data


def test_wellknown_nodeinfo(db, preferences, api_client, settings):
    expected = {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": "{}{}".format(
                    settings.FUNKWHALE_URL, reverse("api:v1:instance:nodeinfo-2.0")
                ),
            }
        ]
    }
    url = reverse("federation:well-known-nodeinfo")
    response = api_client.get(url, HTTP_ACCEPT="application/jrd+json")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/jrd+json"
    assert response.data == expected


def test_wellknown_nodeinfo_disabled(db, preferences, api_client):
    preferences["instance__nodeinfo_enabled"] = False
    url = reverse("federation:well-known-nodeinfo")
    response = api_client.get(url)
    assert response.status_code == 404


def test_audio_file_list_requires_authenticated_actor(db, preferences, api_client):
    preferences["federation__music_needs_approval"] = True
    url = reverse("federation:music:files-list")
    response = api_client.get(url)

    assert response.status_code == 403


def test_audio_file_list_actor_no_page(db, preferences, api_client, factories):
    preferences["federation__music_needs_approval"] = False
    preferences["federation__collection_page_size"] = 2
    library = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    tfs = factories["music.TrackFile"].create_batch(size=5)
    conf = {
        "id": utils.full_url(reverse("federation:music:files-list")),
        "page_size": 2,
        "items": list(reversed(tfs)),  # we order by -creation_date
        "item_serializer": serializers.AudioSerializer,
        "actor": library,
    }
    expected = serializers.PaginatedCollectionSerializer(conf).data
    url = reverse("federation:music:files-list")
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == expected


def test_audio_file_list_actor_page(db, preferences, api_client, factories):
    preferences["federation__music_needs_approval"] = False
    preferences["federation__collection_page_size"] = 2
    library = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    tfs = factories["music.TrackFile"].create_batch(size=5)
    conf = {
        "id": utils.full_url(reverse("federation:music:files-list")),
        "page": Paginator(list(reversed(tfs)), 2).page(2),
        "item_serializer": serializers.AudioSerializer,
        "actor": library,
    }
    expected = serializers.CollectionPageSerializer(conf).data
    url = reverse("federation:music:files-list")
    response = api_client.get(url, data={"page": 2})

    assert response.status_code == 200
    assert response.data == expected


def test_audio_file_list_actor_page_exclude_federated_files(
    db, preferences, api_client, factories
):
    preferences["federation__music_needs_approval"] = False
    factories["music.TrackFile"].create_batch(size=5, federation=True)

    url = reverse("federation:music:files-list")
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data["totalItems"] == 0


def test_audio_file_list_actor_page_error(db, preferences, api_client, factories):
    preferences["federation__music_needs_approval"] = False
    url = reverse("federation:music:files-list")
    response = api_client.get(url, data={"page": "nope"})

    assert response.status_code == 400


def test_audio_file_list_actor_page_error_too_far(
    db, preferences, api_client, factories
):
    preferences["federation__music_needs_approval"] = False
    url = reverse("federation:music:files-list")
    response = api_client.get(url, data={"page": 5000})

    assert response.status_code == 404


def test_library_actor_includes_library_link(db, preferences, api_client):
    url = reverse("federation:instance-actors-detail", kwargs={"actor": "library"})
    response = api_client.get(url)
    expected_links = [
        {
            "type": "Link",
            "name": "library",
            "mediaType": "application/activity+json",
            "href": utils.full_url(reverse("federation:music:files-list")),
        }
    ]
    assert response.status_code == 200
    assert response.data["url"] == expected_links


def test_can_fetch_library(superuser_api_client, mocker):
    result = {"test": "test"}
    scan = mocker.patch(
        "funkwhale_api.federation.library.scan_from_account_name", return_value=result
    )

    url = reverse("api:v1:federation:libraries-fetch")
    response = superuser_api_client.get(url, data={"account": "test@test.library"})

    assert response.status_code == 200
    assert response.data == result
    scan.assert_called_once_with("test@test.library")


def test_follow_library(superuser_api_client, mocker, factories, r_mock):
    library_actor = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    actor = factories["federation.Actor"]()
    follow = {"test": "follow"}
    on_commit = mocker.patch("funkwhale_api.common.utils.on_commit")
    actor_data = serializers.ActorSerializer(actor).data
    actor_data["url"] = [
        {"href": "https://test.library", "name": "library", "type": "Link"}
    ]
    library_conf = {
        "id": "https://test.library",
        "items": range(10),
        "actor": actor,
        "page_size": 5,
    }
    library_data = serializers.PaginatedCollectionSerializer(library_conf).data
    r_mock.get(actor.url, json=actor_data)
    r_mock.get("https://test.library", json=library_data)
    data = {
        "actor": actor.url,
        "autoimport": False,
        "federation_enabled": True,
        "download_files": False,
    }

    url = reverse("api:v1:federation:libraries-list")
    response = superuser_api_client.post(url, data)

    assert response.status_code == 201

    follow = models.Follow.objects.get(actor=library_actor, target=actor, approved=None)
    library = follow.library

    assert response.data == serializers.APILibraryCreateSerializer(library).data

    on_commit.assert_called_once_with(
        activity.deliver,
        serializers.FollowSerializer(follow).data,
        on_behalf_of=library_actor,
        to=[actor.url],
    )


def test_can_list_system_actor_following(factories, superuser_api_client):
    library_actor = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    follow1 = factories["federation.Follow"](actor=library_actor)
    factories["federation.Follow"]()

    url = reverse("api:v1:federation:libraries-following")
    response = superuser_api_client.get(url)

    assert response.status_code == 200
    assert response.data["results"] == [serializers.APIFollowSerializer(follow1).data]


def test_can_list_system_actor_followers(factories, superuser_api_client):
    library_actor = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    factories["federation.Follow"](actor=library_actor)
    follow2 = factories["federation.Follow"](target=library_actor)

    url = reverse("api:v1:federation:libraries-followers")
    response = superuser_api_client.get(url)

    assert response.status_code == 200
    assert response.data["results"] == [serializers.APIFollowSerializer(follow2).data]


def test_can_list_libraries(factories, superuser_api_client):
    library1 = factories["federation.Library"]()
    library2 = factories["federation.Library"]()

    url = reverse("api:v1:federation:libraries-list")
    response = superuser_api_client.get(url)

    assert response.status_code == 200
    assert response.data["results"] == [
        serializers.APILibrarySerializer(library1).data,
        serializers.APILibrarySerializer(library2).data,
    ]


def test_can_detail_library(factories, superuser_api_client):
    library = factories["federation.Library"]()

    url = reverse(
        "api:v1:federation:libraries-detail", kwargs={"uuid": str(library.uuid)}
    )
    response = superuser_api_client.get(url)

    assert response.status_code == 200
    assert response.data == serializers.APILibrarySerializer(library).data


def test_can_patch_library(factories, superuser_api_client):
    library = factories["federation.Library"]()
    data = {
        "federation_enabled": not library.federation_enabled,
        "download_files": not library.download_files,
        "autoimport": not library.autoimport,
    }
    url = reverse(
        "api:v1:federation:libraries-detail", kwargs={"uuid": str(library.uuid)}
    )
    response = superuser_api_client.patch(url, data)

    assert response.status_code == 200
    library.refresh_from_db()

    for k, v in data.items():
        assert getattr(library, k) == v


def test_scan_library(factories, mocker, superuser_api_client):
    scan = mocker.patch(
        "funkwhale_api.federation.tasks.scan_library.delay",
        return_value=mocker.Mock(id="id"),
    )
    library = factories["federation.Library"]()
    now = timezone.now()
    data = {"until": now}
    url = reverse(
        "api:v1:federation:libraries-scan", kwargs={"uuid": str(library.uuid)}
    )
    response = superuser_api_client.post(url, data)

    assert response.status_code == 200
    assert response.data == {"task": "id"}
    scan.assert_called_once_with(library_id=library.pk, until=now)


def test_list_library_tracks(factories, superuser_api_client):
    library = factories["federation.Library"]()
    lts = list(
        reversed(
            factories["federation.LibraryTrack"].create_batch(size=5, library=library)
        )
    )
    factories["federation.LibraryTrack"].create_batch(size=5)
    url = reverse("api:v1:federation:library-tracks-list")
    response = superuser_api_client.get(url, {"library": library.uuid})

    assert response.status_code == 200
    assert response.data == {
        "results": serializers.APILibraryTrackSerializer(lts, many=True).data,
        "count": 5,
        "previous": None,
        "next": None,
    }


def test_can_update_follow_status(factories, superuser_api_client, mocker):
    patched_accept = mocker.patch("funkwhale_api.federation.activity.accept_follow")
    library_actor = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    follow = factories["federation.Follow"](target=library_actor)

    payload = {"follow": follow.pk, "approved": True}
    url = reverse("api:v1:federation:libraries-followers")
    response = superuser_api_client.patch(url, payload)
    follow.refresh_from_db()

    assert response.status_code == 200
    assert follow.approved is True
    patched_accept.assert_called_once_with(follow)


def test_can_filter_pending_follows(factories, superuser_api_client):
    library_actor = actors.SYSTEM_ACTORS["library"].get_actor_instance()
    factories["federation.Follow"](target=library_actor, approved=True)

    params = {"pending": True}
    url = reverse("api:v1:federation:libraries-followers")
    response = superuser_api_client.get(url, params)

    assert response.status_code == 200
    assert len(response.data["results"]) == 0


def test_library_track_action_import(factories, superuser_api_client, mocker):
    lt1 = factories["federation.LibraryTrack"]()
    lt2 = factories["federation.LibraryTrack"](library=lt1.library)
    lt3 = factories["federation.LibraryTrack"]()
    factories["federation.LibraryTrack"](library=lt3.library)
    mocked_run = mocker.patch("funkwhale_api.music.tasks.import_batch_run.delay")

    payload = {
        "objects": "all",
        "action": "import",
        "filters": {"library": lt1.library.uuid},
    }
    url = reverse("api:v1:federation:library-tracks-action")
    response = superuser_api_client.post(url, payload, format="json")
    batch = superuser_api_client.user.imports.latest("id")
    expected = {"updated": 2, "action": "import", "result": {"batch": {"id": batch.pk}}}

    imported_lts = [lt1, lt2]
    assert response.status_code == 200
    assert response.data == expected
    assert batch.jobs.count() == 2
    for i, job in enumerate(batch.jobs.all()):
        assert job.library_track == imported_lts[i]
    mocked_run.assert_called_once_with(import_batch_id=batch.pk)


def test_local_actor_detail(factories, api_client):
    user = factories["users.User"](with_actor=True)
    url = reverse("federation:actors-detail", kwargs={"user__username": user.username})
    serializer = serializers.ActorSerializer(user.actor)
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data == serializer.data


def test_wellknown_webfinger_local(factories, api_client, settings, mocker):
    user = factories["users.User"](with_actor=True)
    url = reverse("federation:well-known-webfinger")
    response = api_client.get(
        url,
        data={"resource": "acct:{}".format(user.actor.webfinger_subject)},
        HTTP_ACCEPT="application/jrd+json",
    )
    serializer = serializers.ActorWebfingerSerializer(user.actor)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/jrd+json"
    assert response.data == serializer.data
