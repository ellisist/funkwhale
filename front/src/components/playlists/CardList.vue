<template>
  <div
    v-if="playlists.length > 0"
    v-masonry
    transition-duration="0"
    item-selector=".column"
    percent-position="true"
    stagger="0"
    class="ui stackable three column doubling grid">
    <div
      v-masonry-tile
      v-for="playlist in playlists"
      :key="playlist.id"
      class="column">
      <playlist-card class="fluid" :playlist="playlist"></playlist-card>
    </div>
  </div>
</template>

<script>

import PlaylistCard from '@/components/playlists/Card'

export default {
  props: ['playlists'],
  components: {
    PlaylistCard
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
