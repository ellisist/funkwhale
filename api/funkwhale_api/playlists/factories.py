import factory

from funkwhale_api.factories import registry
from funkwhale_api.music.factories import TrackFactory
from funkwhale_api.users.factories import UserFactory


@registry.register
class PlaylistFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = "playlists.Playlist"


@registry.register
class PlaylistTrackFactory(factory.django.DjangoModelFactory):
    playlist = factory.SubFactory(PlaylistFactory)
    track = factory.SubFactory(TrackFactory)

    class Meta:
        model = "playlists.PlaylistTrack"
