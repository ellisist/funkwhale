<template>
  <div class="main pusher" v-title="labels.title">
    <div class="ui vertical stripe segment">
      <div class="ui small text container">
        <h2><translate>Log in to your Funkwhale account</translate></h2>
        <form class="ui form" @submit.prevent="submit()">
          <div v-if="error" class="ui negative message">
            <div class="header"><translate>We cannot log you in</translate></div>
            <ul class="list">
              <li v-if="error == 'invalid_credentials'"><translate>Please double-check your username/password couple is correct</translate></li>
              <li v-else><translate>An unknown error happend, this can mean the server is down or cannot be reached</translate></li>
            </ul>
          </div>
          <div class="field">
            <label>
              <translate>Username or email</translate> |
              <router-link :to="{path: '/signup'}">
                <translate>Create an account</translate>
              </router-link>
            </label>
            <input
            ref="username"
            tabindex="1"
            required
            type="text"
            autofocus
            :placeholder="labels.usernamePlaceholder"
            v-model="credentials.username"
            >
          </div>
          <div class="field">
            <label>
              <translate>Password</translate> |
              <router-link :to="{name: 'auth.password-reset', query: {email: credentials.username}}">
                <translate>Reset your password</translate>
              </router-link>
            </label>
            <password-input :index="2" required v-model="credentials.password" />

          </div>
          <button tabindex="3" :class="['ui', {'loading': isLoading}, 'right', 'floated', 'green', 'button']" type="submit">
             <translate>Login</translate>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import PasswordInput from '@/components/forms/PasswordInput'

export default {
  props: {
    next: {type: String, default: '/'}
  },
  components: {
    PasswordInput
  },
  data () {
    return {
      // We need to initialize the component with any
      // properties that will be used in it
      credentials: {
        username: '',
        password: ''
      },
      error: '',
      isLoading: false
    }
  },
  mounted () {
    this.$refs.username.focus()
  },
  computed: {
    labels () {
      let usernamePlaceholder = this.$gettext('Enter your username or email')
      let title = this.$gettext('Log In')
      return {
        usernamePlaceholder,
        title
      }
    }
  },
  methods: {
    submit () {
      var self = this
      self.isLoading = true
      this.error = ''
      var credentials = {
        username: this.credentials.username,
        password: this.credentials.password
      }
      this.$store.dispatch('auth/login', {
        credentials,
        next: '/library',
        onError: error => {
          if (error.response.status === 400) {
            self.error = 'invalid_credentials'
          } else {
            self.error = 'unknown_error'
          }
        }
      }).then(e => {
        self.isLoading = false
      })
    }
  }

}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
