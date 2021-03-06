from django.urls import reverse

from funkwhale_api.music import lyrics as lyrics_utils
from funkwhale_api.music import models, tasks


def test_lyrics_tasks(lyricswiki_content, mocker, factories):
    mocker.patch(
        "funkwhale_api.music.lyrics._get_html", return_value=lyricswiki_content
    )
    lyrics = factories["music.Lyrics"](
        url="http://lyrics.wikia.com/System_Of_A_Down:Chop_Suey!"
    )

    tasks.fetch_content(lyrics_id=lyrics.pk)
    lyrics.refresh_from_db()
    assert "Grab a brush and put on a little makeup" in lyrics.content


def test_clean_content():
    c = """<div class="lyricbox">Hello<br /><script>alert('hello');</script>Is it me you're looking for?<br /></div>"""
    d = lyrics_utils.extract_content(c)
    d = lyrics_utils.clean_content(d)

    expected = """Hello
Is it me you're looking for?
"""
    assert d == expected


def test_markdown_rendering(factories):
    content = """Hello
Is it me you're looking for?"""

    lyrics = factories["music.Lyrics"](content=content)

    expected = "<p>Hello<br />\nIs it me you're looking for?</p>"
    assert expected == lyrics.content_rendered


def test_works_import_lyrics_if_any(
    lyricswiki_content, works, tracks, mocker, factories, logged_in_client
):
    mocker.patch(
        "funkwhale_api.musicbrainz.api.works.get",
        return_value=works["get"]["chop_suey"],
    )
    mocker.patch(
        "funkwhale_api.musicbrainz.api.recordings.get",
        return_value=tracks["get"]["chop_suey"],
    )
    mocker.patch(
        "funkwhale_api.music.lyrics._get_html", return_value=lyricswiki_content
    )
    track = factories["music.Track"](
        work=None, mbid="07ca77cf-f513-4e9c-b190-d7e24bbad448"
    )

    url = reverse("api:v1:tracks-lyrics", kwargs={"pk": track.pk})
    response = logged_in_client.get(url)

    assert response.status_code == 200

    track.refresh_from_db()
    lyrics = models.Lyrics.objects.latest("id")
    work = models.Work.objects.latest("id")

    assert track.work == work
    assert lyrics.work == work
