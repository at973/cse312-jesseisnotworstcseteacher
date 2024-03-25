function newChat(chatJSON) {
    const username = chatJSON.username;
    const message = chatJSON.message;
    const id = chatJSON.id;
    const message_html = 
        `<div class="tile is-vertical m-2 sent-message-box">
            <article class="message is-primary" id=${id}>
                <div class="message-body"><b>${username}: </b> ${message} </div>
            </article>
        </div>
        `;
    return message_html;
}

function clearChat() {
    document.getElementById("chatbox").innerHTML = "";
}

function updateChat() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const messages = JSON.parse(this.response);
            for (const message of messages) {
                document.getElementById("chatbox").innerHTML += newChat(message);
            }
        }
    }
    request.open("GET", "/messages");
    request.send();
}

function generateTestChats() {
    chats = '';
    for(let i = 0; i < 50; i++) {
        chats += newChat({username: 'guest', message: 'this is just a test', id: i});
    }
    console.log('chats', chats);
    document.getElementById('chatbox').innerHTML = chats;
}

function welcome() {
    // generateTestChats();  // Line is only here for tests
    updateChat();
    setInterval(updateChat, 5000);
}
