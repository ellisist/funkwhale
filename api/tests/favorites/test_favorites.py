import json

import pytest
from django.urls import reverse

from funkwhale_api.favorites.models import TrackFavorite
from funkwhale_api.music import serializers as music_serializers
from funkwhale_api.users import serializers as users_serializers


def test_user_can_add_favorite(factories):
    track = factories["music.Track"]()
    user = factories["users.User"]()
    f = TrackFavorite.add(track, user)

    assert f.track == track
    assert f.user == user


def test_user_can_get_his_favorites(api_request, factories, logged_in_client, client):
    r = api_request.get("/")
    favorite = factories["favorites.TrackFavorite"](user=logged_in_client.user)
    factories["favorites.TrackFavorite"]()
    url = reverse("api:v1:favorites:tracks-list")
    response = logged_in_client.get(url, {"user": logged_in_client.user.pk})
    expected = [
        {
            "user": users_serializers.UserBasicSerializer(
                favorite.user, context={"request": r}
            ).data,
            "track": music_serializers.TrackSerializer(
                favorite.track, context={"request": r}
            ).data,
            "id": favorite.id,
            "creation_date": favorite.creation_date.isoformat().replace("+00:00", "Z"),
        }
    ]
    expected[0]["track"]["is_playable"] = False
    assert response.status_code == 200
    assert response.data["results"] == expected


def test_user_can_add_favorite_via_api(factories, logged_in_client, activity_muted):
    track = factories["music.Track"]()
    url = reverse("api:v1:favorites:tracks-list")
    response = logged_in_client.post(url, {"track": track.pk})

    favorite = TrackFavorite.objects.latest("id")
    expected = {
        "track": track.pk,
        "id": favorite.id,
        "creation_date": favorite.creation_date.isoformat().replace("+00:00", "Z"),
    }
    parsed_json = json.loads(response.content.decode("utf-8"))

    assert expected == parsed_json
    assert favorite.track == track
    assert favorite.user == logged_in_client.user


def test_adding_favorites_calls_activity_record(
    factories, logged_in_client, activity_muted
):
    track = factories["music.Track"]()
    url = reverse("api:v1:favorites:tracks-list")
    response = logged_in_client.post(url, {"track": track.pk})

    favorite = TrackFavorite.objects.latest("id")
    expected = {
        "track": track.pk,
        "id": favorite.id,
        "creation_date": favorite.creation_date.isoformat().replace("+00:00", "Z"),
    }
    parsed_json = json.loads(response.content.decode("utf-8"))

    assert expected == parsed_json
    assert favorite.track == track
    assert favorite.user == logged_in_client.user

    activity_muted.assert_called_once_with(favorite)


def test_user_can_remove_favorite_via_api(logged_in_client, factories, client):
    favorite = factories["favorites.TrackFavorite"](user=logged_in_client.user)
    url = reverse("api:v1:favorites:tracks-detail", kwargs={"pk": favorite.pk})
    response = client.delete(url, {"track": favorite.track.pk})
    assert response.status_code == 204
    assert TrackFavorite.objects.count() == 0


@pytest.mark.parametrize("method", ["delete", "post"])
def test_user_can_remove_favorite_via_api_using_track_id(
    method, factories, logged_in_client
):
    favorite = factories["favorites.TrackFavorite"](user=logged_in_client.user)

    url = reverse("api:v1:favorites:tracks-remove")
    response = getattr(logged_in_client, method)(
        url, json.dumps({"track": favorite.track.pk}), content_type="application/json"
    )

    assert response.status_code == 204
    assert TrackFavorite.objects.count() == 0


@pytest.mark.parametrize("url,method", [("api:v1:favorites:tracks-list", "get")])
def test_url_require_auth(url, method, db, preferences, client):
    preferences["common__api_authentication_required"] = True
    url = reverse(url)
    response = getattr(client, method)(url)
    assert response.status_code == 401


def test_can_filter_tracks_by_favorites(factories, logged_in_client):
    favorite = factories["favorites.TrackFavorite"](user=logged_in_client.user)

    url = reverse("api:v1:tracks-list")
    response = logged_in_client.get(url, data={"favorites": True})

    parsed_json = json.loads(response.content.decode("utf-8"))
    assert parsed_json["count"] == 1
    assert parsed_json["results"][0]["id"] == favorite.track.id
