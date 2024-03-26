function newChat(chatJSON) {
    const username = chatJSON.username;
    const message = chatJSON.message;
    const id = chatJSON.id;
    const likes = chatJSON.likes;
    const message_html = 
        `<div class="tile is-vertical m-2 sent-message-box">
            <article class="message is-primary" id=${id}>
                <div class="message-body"><b>${username}: </b> ${message} </div>
                <div class="tile is-horizontal m-2 message-interaction-box">
                <div class="column"><label>${likes} Likes <\label></div>
                    <div class="column">
                        <form action="/like" method="post" enctype="application/x-www-form-urlencoded">
                            <input value = "${id}" type="hidden" name="id">
                            <input type="submit" value="Like">
                        </form>
                    </div>
                </div>
            </article>
        <\div>
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
    for(let i = 0; i < 1; i++) {
        longmsg = "this is a ridiculously long message in an attempt to try to see if anything would happen if the string were to take up additional lines, and potentially break the display. If something looks broken, that means that you did something wrong, and that's unfortunate :(";
        chats += newChat({username: 'guest', message: 'this is just a test', id: i});
        chats += newChat({username: 'guest', message: longmsg, id: i});
    }
    console.log('chats', chats);
    document.getElementById('chatbox').innerHTML = chats;
}

function welcome() {
    // generateTestChats();  // Line is only here for tests
    updateChat();
    setInterval(updateChat, 5000);
}
