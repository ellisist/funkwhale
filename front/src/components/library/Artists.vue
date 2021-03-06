<template>
  <div v-title="labels.title">
    <div class="ui vertical stripe segment">
      <h2 class="ui header">
        <translate>Browsing artists</translate>
      </h2>
      <div :class="['ui', {'loading': isLoading}, 'form']">
        <div class="fields">
          <div class="field">
            <label>
              <translate>Search</translate>
            </label>
            <input type="text" v-model="query" :placeholder="labels.searchPlaceholder"/>
          </div>
          <div class="field">
            <label><translate>Ordering</translate></label>
            <select class="ui dropdown" v-model="ordering">
              <option v-for="option in orderingOptions" :value="option[0]">
                {{ sharedLabels.filters[option[1]] }}
              </option>
            </select>
          </div>
          <div class="field">
            <label><translate>Ordering direction</translate></label>
            <select class="ui dropdown" v-model="orderingDirection">
              <option value="+"><translate>Ascending</translate></option>
              <option value="-"><translate>Descending</translate></option>
            </select>
          </div>
          <div class="field">
            <label><translate>Results per page</translate></label>
            <select class="ui dropdown" v-model="paginateBy">
              <option :value="parseInt(12)">12</option>
              <option :value="parseInt(25)">25</option>
              <option :value="parseInt(50)">50</option>
            </select>
          </div>
        </div>
      </div>
      <div class="ui hidden divider"></div>
      <div
        v-if="result"
        v-masonry
        transition-duration="0"
        item-selector=".column"
        percent-position="true"
        stagger="0"
        class="ui stackable three column doubling grid">
        <div
          v-masonry-tile
          v-if="result.results.length > 0"
          v-for="artist in result.results"
          :key="artist.id"
          class="column">
          <artist-card class="fluid" :artist="artist"></artist-card>
        </div>
      </div>
      <div class="ui center aligned basic segment">
        <pagination
          v-if="result && result.count > paginateBy"
          @page-changed="selectPage"
          :current="page"
          :paginate-by="paginateBy"
          :total="result.count"
          ></pagination>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import _ from 'lodash'
import $ from 'jquery'

import logger from '@/logging'

import OrderingMixin from '@/components/mixins/Ordering'
import PaginationMixin from '@/components/mixins/Pagination'
import TranslationsMixin from '@/components/mixins/Translations'
import ArtistCard from '@/components/audio/artist/Card'
import Pagination from '@/components/Pagination'

const FETCH_URL = 'artists/'

export default {
  mixins: [OrderingMixin, PaginationMixin, TranslationsMixin],
  props: {
    defaultQuery: {type: String, required: false, default: ''}
  },
  components: {
    ArtistCard,
    Pagination
  },
  data () {
    let defaultOrdering = this.getOrderingFromString(this.defaultOrdering || '-creation_date')
    return {
      isLoading: true,
      result: null,
      page: parseInt(this.defaultPage),
      query: this.defaultQuery,
      paginateBy: parseInt(this.defaultPaginateBy || 12),
      orderingDirection: defaultOrdering.direction || '+',
      ordering: defaultOrdering.field,
      orderingOptions: [
        ['creation_date', 'creation_date'],
        ['name', 'name']
      ]
    }
  },
  created () {
    this.fetchData()
  },
  mounted () {
    $('.ui.dropdown').dropdown()
  },
  computed: {
    labels () {
      let searchPlaceholder = this.$gettext('Enter an artist name...')
      let title = this.$gettext('Artists')
      return {
        searchPlaceholder,
        title
      }
    }
  },
  methods: {
    updateQueryString: _.debounce(function () {
      this.$router.replace({
        query: {
          query: this.query,
          page: this.page,
          paginateBy: this.paginateBy,
          ordering: this.getOrderingAsString()
        }
      })
    }, 500),
    fetchData: _.debounce(function () {
      var self = this
      this.isLoading = true
      let url = FETCH_URL
      let params = {
        page: this.page,
        page_size: this.paginateBy,
        name__icontains: this.query,
        ordering: this.getOrderingAsString(),
        playable: 'true'
      }
      logger.default.debug('Fetching artists')
      axios.get(url, {params: params}).then((response) => {
        self.result = response.data
        self.isLoading = false
      })
    }, 500),
    selectPage: function (page) {
      this.page = page
    }
  },
  watch: {
    page () {
      this.updateQueryString()
      this.fetchData()
    },
    paginateBy () {
      this.updateQueryString()
      this.fetchData()
    },
    ordering () {
      this.updateQueryString()
      this.fetchData()
    },
    orderingDirection () {
      this.updateQueryString()
      this.fetchData()
    },
    query () {
      this.updateQueryString()
      this.fetchData()
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
