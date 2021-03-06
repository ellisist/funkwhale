<template>
  <div class="ui fluid category search">
    <slot></slot><div class="ui icon input">
      <input class="prompt" :placeholder="labels.placeholder" type="text">
      <i class="search icon"></i>
    </div>
    <div class="results"></div>
    <slot name="after"></slot>
  </div>
</template>

<script>
import jQuery from 'jquery'
import router from '@/router'

export default {
  computed: {
    labels () {
      return {
        placeholder: this.$gettext('Search for artists, albums, tracks...')
      }
    }
  },
  mounted () {
    let artistLabel = this.$gettext('Artist')
    let albumLabel = this.$gettext('Album')
    let trackLabel = this.$gettext('Track')
    let self = this
    jQuery(this.$el).search({
      type: 'category',
      minCharacters: 3,
      onSelect (result, response) {
        router.push(result.routerUrl)
      },
      onSearchQuery (query) {
        self.$emit('search')
      },
      apiSettings: {
        beforeXHR: function (xhrObject) {
          if (!self.$store.state.auth.authenticated) {
            return xhrObject
          }
          xhrObject.setRequestHeader('Authorization', self.$store.getters['auth/header'])
          return xhrObject
        },
        onResponse: function (initialResponse) {
          var results = {}
          let categories = [
            {
              code: 'artists',
              route: 'library.artists.detail',
              name: artistLabel,
              getTitle (r) {
                return r.name
              },
              getDescription (r) {
                return ''
              }
            },
            {
              code: 'albums',
              route: 'library.albums.detail',
              name: albumLabel,
              getTitle (r) {
                return r.title
              },
              getDescription (r) {
                return ''
              }
            },
            {
              code: 'tracks',
              route: 'library.tracks.detail',
              name: trackLabel,
              getTitle (r) {
                return r.title
              },
              getDescription (r) {
                return ''
              }
            }
          ]
          categories.forEach(category => {
            results[category.code] = {
              name: category.name,
              results: []
            }
            initialResponse[category.code].forEach(result => {
              results[category.code].results.push({
                title: category.getTitle(result),
                id: result.id,
                routerUrl: {
                  name: category.route,
                  params: {
                    id: result.id
                  }
                },
                description: category.getDescription(result)
              })
            })
          })
          return {results: results}
        },
        url: this.$store.getters['instance/absoluteUrl']('api/v1/search?query={query}')
      }
    })
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
