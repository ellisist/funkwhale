<template>
  <div v-title="labels.users">
    <div class="ui vertical stripe segment">
      <h2 class="ui header"><translate>Users</translate></h2>
      <div class="ui hidden divider"></div>
      <users-table></users-table>
    </div>
  </div>
</template>

<script>
import UsersTable from '@/components/manage/users/UsersTable'

export default {
  components: {
    UsersTable
  },
  computed: {
    labels () {
      return {
        users: this.$gettext('Users')
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
