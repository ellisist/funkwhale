<template>
  <div>
    <div v-if="isLoading" class="ui vertical segment">
      <div :class="['ui', 'centered', 'active', 'inline', 'loader']"></div>
    </div>
    <template v-if="object">
      <div :class="['ui', 'head', 'vertical', 'center', 'aligned', 'stripe', 'segment']" v-title="object.username">
        <div class="segment-content">
          <h2 class="ui center aligned icon header">
            <i class="circular inverted user red icon"></i>
            <div class="content">
              @{{ object.username }}
            </div>
          </h2>
        </div>
        <div class="ui hidden divider"></div>
        <div class="ui one column centered grid">
          <table class="ui collapsing very basic table">
            <tbody>
              <tr>
                <td>
                  {{ $t('Name') }}
                </td>
                <td>
                  {{ object.name }}
                </td>
              </tr>
              <tr>
                <td>
                  {{ $t('Email address') }}
                </td>
                <td>
                  {{ object.email }}
                </td>
              </tr>
              <tr>
                <td>
                  {{ $t('Sign-up') }}
                </td>
                <td>
                  <human-date :date="object.date_joined"></human-date>
                </td>
              </tr>
              <tr>
                <td>
                  {{ $t('Last activity') }}
                </td>
                <td>
                  <human-date v-if="object.last_activity" :date="object.last_activity"></human-date>
                  <template v-else>{{ $t('N/A') }}</template>
                </td>
              </tr>
              <tr>
                <td>
                  {{ $t('Account active') }}
                  <span :data-tooltip="$t('Determine if the user account is active or not. Inactive users cannot login or user the service.')"><i class="question circle icon"></i></span>
                </td>
                <td>
                  <div class="ui toggle checkbox">
                    <input
                      @change="update('is_active')"
                      v-model="object.is_active" type="checkbox">
                    <label></label>
                  </div>
                </td>
              </tr>
              <tr>
                <td>
                  {{ $t('Permissions') }}
                </td>
                <td>
                  <select
                    @change="update('permissions')"
                    v-model="permissions"
                    multiple
                    class="ui search selection dropdown">
                    <option v-for="p in allPermissions" :value="p.code">{{ p.label }}</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="ui hidden divider"></div>
        <button @click="fetchData" class="ui basic button">{{ $t('Refresh') }}</button>
      </div>
    </template>
  </div>
</template>

<script>

import $ from 'jquery'
import axios from 'axios'
import logger from '@/logging'

export default {
  props: ['id'],
  data () {
    return {
      isLoading: true,
      object: null,
      permissions: []
    }
  },
  created () {
    this.fetchData()
  },
  methods: {
    fetchData () {
      var self = this
      this.isLoading = true
      let url = 'manage/users/users/' + this.id + '/'
      axios.get(url).then((response) => {
        self.object = response.data
        self.permissions = []
        self.allPermissions.forEach(p => {
          if (self.object.permissions[p.code]) {
            self.permissions.push(p.code)
          }
        })
        self.isLoading = false
      })
    },
    update (attr) {
      let newValue = this.object[attr]
      let params = {}
      if (attr === 'permissions') {
        params['permissions'] = {}
        this.allPermissions.forEach(p => {
          params['permissions'][p.code] = this.permissions.indexOf(p.code) > -1
        })
      } else {
        params[attr] = newValue
      }
      axios.patch('manage/users/users/' + this.id + '/', params).then((response) => {
        logger.default.info(`${attr} was updated succcessfully to ${newValue}`)
      }, (error) => {
        logger.default.error(`Error while setting ${attr} to ${newValue}`, error)
      })
    }
  },
  computed: {
    allPermissions () {
      return [
        {
          'code': 'upload',
          'label': this.$t('Upload')
        },
        {
          'code': 'library',
          'label': this.$t('Library')
        },
        {
          'code': 'federation',
          'label': this.$t('Federation')
        },
        {
          'code': 'settings',
          'label': this.$t('Settings')
        }
      ]
    }
  },
  watch: {
    object () {
      this.$nextTick(() => {
        $('select.dropdown').dropdown()
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>