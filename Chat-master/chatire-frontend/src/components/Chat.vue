<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-6 offset-3">

        <div v-if="!loading && sessionStarted" id="chat-container" class="card">
          <div class="card-header text-white text-center font-weight-bold subtle-blue-gradient">
            Share the page URL to invite new friends
          </div>

          <div class="card-body">
            <div class="container chat-body" ref="chatBody">
              <div v-for="message in messages" :key="message.id" class="row chat-section">
                <template v-if="username === message.user.username">
                  <div class="col-sm-7 offset-3">
                    <span class="card-text speech-bubble speech-bubble-user float-right text-white subtle-blue-gradient">
                      {{ message.message }}
                    </span>
                  </div>
                  <div class="col-sm-2">
                    <img class="rounded-circle" :src="`http://placehold.it/40/007bff/fff&text=${message.user.username[0].toUpperCase()}`" />
                  </div>
                </template>
                <template v-else>
                  <div class="col-sm-2">
                    <img class="rounded-circle" :src="`http://placehold.it/40/333333/fff&text=${message.user.username[0].toUpperCase()}`" />
                  </div>
                  <div class="col-sm-7">
                    <span class="card-text speech-bubble speech-bubble-peer">
                      {{ message.message }}
                    </span>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <div class="card-footer text-muted">
            <form @submit.prevent="postMessage">
              <div class="row">
                <div class="col-sm-10">
                  <input v-model="message" type="text" placeholder="Type a message" />
                </div>
                <div class="col-sm-2">
                  <button class="btn btn-primary">Send</button>
                </div>
              </div>
            </form>
          </div>
        </div>

        <div v-else-if="!loading && !sessionStarted">
          <h3 class="text-center">Welcome {{ username }}!</h3>
          <br />
          <p class="text-center">
            To start chatting with friends click on the button below, it'll start a new chat session
            and then you can invite your friends over to chat!
          </p>
          <br />
          <button @click="startChatSession" class="btn btn-primary btn-lg btn-block">Start Chatting</button>
        </div>

        <div v-else>
          <div class="loading">
            <img src="../assets/disqus.svg" />
            <h4>Loading...</h4>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

const $ = window.jQuery

export default {
  data () {
    return {
      loading: true,
      messages: [],
      message: '',
      notification: new Audio('../../static/plucky.ogg'),
      sessionStarted: false
    }
  },

  created () {
    this.username = sessionStorage.getItem('username')

    // Setup headers for all requests
    $.ajaxSetup({
      beforeSend: function (xhr) {
        xhr.setRequestHeader('Authorization', `JWT ${sessionStorage.getItem('authToken')}`)
      }
    })

    if (this.$route.params.uri) {
      this.joinChatSession()
      this.connectToWebSocket()
    }

    setTimeout(() => { this.loading = false }, 2000)

    // Refresh the JWT every 240 Seconds (4 minutes)
    setInterval(this.refreshToken, 240000)

    setInterval(this.fetchChatSessionHistory, 4000)
  },

  updated () {
    // Scroll to bottom of Chat window
    const chatBody = this.$refs.chatBody
    if (chatBody) {
      chatBody.scrollTop = chatBody.scrollHeight
    }
  },

  methods: {
    startChatSession () {
      $.post('http://localhost:8000/api/chats/', (data) => {
        alert("A new session has been created you'll be redirected automatically")
        this.sessionStarted = true
        this.$router.push(`/chats/${data.uri}/`)
        this.connectToWebSocket()
      })
      .fail((response) => {
        alert(response.responseText)
      })
    },

    postMessage (event) {
      const data = {message: this.message}

      $.post(`http://localhost:8000/api/chats/${this.$route.params.uri}/messages/`, data, (data) => {
        this.message = '' // clear the message after sending
      })
      .fail((response) => {
        alert(response.responseText)
      })
    },

    joinChatSession () {
      const uri = this.$route.params.uri

      $.ajax({
        url: `http://localhost:8000/api/chats/${uri}/`,
        data: {username: this.username},
        type: 'PATCH',
        success: (data) => {
          const user = data.members.find((member) => member.username === this.username)

          if (user) {
            // The user belongs/has joined the session
            this.sessionStarted = true
            this.fetchChatSessionHistory()
          }
        }
      })
    },

    fetchChatSessionHistory () {
      $.get(`http://127.0.0.1:8000/api/chats/${this.$route.params.uri}/messages/`, (data) => {
        this.messages = data.messages
        setTimeout(() => { this.loading = false }, 2000)
        this.$forceUpdate() // Force Vue.js to re-render the component
      })
    },

    connectToWebSocket () {
      const websocket = new WebSocket(`ws://localhost:8081/${this.$route.params.uri}`)
      websocket.onopen = this.onOpen
      websocket.onclose = this.onClose
      websocket.onmessage = this.onMessage
      websocket.onerror = this.onError
    },

    onOpen (event) {
      console.log('Connection opened.', event.data)
    },

    onClose (event) {
      console.log('Connection closed.', event.data)

      // Try and Reconnect after five seconds
      setTimeout(this.connectToWebSocket, 5000)
    },

    onMessage (event) {
      const message = JSON.parse(event.data)
      this.$set(this.messages, this.messages.length, message)

      this.$nextTick(() => {
        const chatBody = this.$refs.chatBody
        if (chatBody) {
          chatBody.scrollTop = chatBody.scrollHeight
        }
      })

      if (!document.hasFocus()) {
        this.notification.play()
      }
    },

    onError (event) {
      alert('An error occured:', event.data)
    },

    refreshToken () {
      const data = {token: sessionStorage.getItem('authToken')}

      $.post('http://127.0.0.1:8000/this/is/hard/to/find/', data, (response) => {
        sessionStorage.setItem('authToken', response.token)
      })
    }
  }
}
</script>

<style scoped>

  /* Typography */
  h1, h2 {
    font-weight: normal;
  }

  ul {
    list-style-type: none;
    padding: 0;
  }

  li {
    display: inline-block;
    margin: 0 10px;
  }

  /* Loading state */
  .loading {
    text-align: center;
    margin-top: 150px;
  }

  /* Buttons */
  .btn {
    border-radius: 0 !important;
  }


  /* Form elements */
  .card-footer input[type="text"] {
    background-color: #ffffff;
    color: #444444;
    padding: 7px;
    font-size: 13px;
    border: 2px solid #cccccc;
    width: 100%;
    height: 38px;
  }

  /* Cards */
  .card-header {
   background-color: var(--primary-color);
   color: #000 !important;
}

  .card-body {
    background-color: #ddd;
  }

  /* Chat bubbles */
  .chat-body {
    margin-top: -15px;
    margin-bottom: -5px;
    height: 380px;
    overflow-y: auto;
    
  }

  .speech-bubble {
    display: inline-block;
    position: relative;
    border-radius: 0.4em;
    padding: 10px;
    background-color: #fff;
    font-size: 14px;
  }

  .subtle-blue-gradient {
    background: linear-gradient(45deg,#4287f5, #007bff);
    color: #000;
      }

  .speech-bubble-user:after {
    content: "";
    position: absolute;
    right: 4px;
    top: 10px;
    width: 0;
    height: 0;
    border: 20px solid transparent;
    border-left-color: #007bff;
    border-right: 0;
    border-top: 0;
    margin-top: -10px;
    margin-right: -20px;
  }

  .speech-bubble-peer:after {
    content: "";
    position: absolute;
    left: 3px;
    top: 10px;
    width: 0;
    height: 0;
    border: 20px solid transparent;
    border-right-color: #ffffff;
    border-top: 0;
    border-left: 0;
    margin-top: -10px;
    margin-left: -20px;
  }

  .chat-section:first-child {
    margin-top: 10px;
  }

  .chat-section {
    margin-top: 15px;
  }

  .send-section {
    margin-bottom: -20px;
    padding-bottom: 10px;
  }

  /* Custom variables */
  :root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
  }

  /* Overrides */
  .card-header.subtle-blue-gradient {
    background: var(--primary-color);
    color: #000;
  }

  .btn-primary {
    opacity: 1 ;
    visibility: visible ;
  }

  .btn-primary:hover {
    background-color: #0056b3;
    border-color: #0056b3;
  }

  input[type="text"]:focus {
    outline-color: var(--primary-color);
    border-color: var(--primary-color);
  }


</style>