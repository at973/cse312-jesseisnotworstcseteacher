const ws = true;
let socket = null;
function newChat(chatJSON) {
    const username = chatJSON.username;
    const message = chatJSON.message;
    const id = chatJSON.id;
    const likes = chatJSON.likes;
    const likefunc = ws ? '/like' : `ws_like(${id})`;
    const new_message_html =
        `<article class="media">
            <figure class="media-left">
                <p class="image is-64x64">
                    <img src="images/default-icon.png" />
                </p>
            </figure>
            <div class="media-content">
                <div class="content">
                    <p> <strong> ${username} </strong> </p>
                    ${message}
                </div>
                <nav class="level">
                    <div class="level-left">
                        <div class="level-item">
                            <form action="/like" method="post" enctype="application/x-www-form-urlencoded">
                                <input value = "${id}" type="hidden" name="id">
                                <buttom type="submit" value="Like" class="button is-ghost">
                                    <span class="icon-text">
                                        <span class="icon"><i class="fa-solid fa-thumbs-up"></i></span>
                                        <span> Like </span>
                                    </span>
                                </button>
                            </form>
                        </div>
                        <div class="level-item">
                            <label>${likes}</label>
                        </div>
                    </div>
                    <div class="level-right">
                    </div>
                </nav>
                <a href="direct_message/${username}">
                    <button class="dm-button" style="background-color: #dddddd;color: black;border: 1px solid black;position: relative;top: -110px; right:-650px">DM</button>
                </a>
            </div>
            <div style="display: block">
                <div class="file is-boxed cell">
                    <label class="file-label">
                        <input class="file-input" type="file" name="resume" />
                        <span class="file-cta">
                            <span class="file-icon">
                                <i class="fas fa-upload"></i>
                            </span>
                            <span class="file-label"> Choose a file… </span>
                        </span>
                    </label>
                </div>

                <div class="cell">
                    <form action="/upload" method="POST" enctype="multipart/form-data">
                        <div class="level-item">
                        </div>
                        <div class="level-item" style="margin: 3px">
                            <button type="submit" class="button is-primary">Add photo to collection</button>
                        </div>
                    </form>
                </div>
            </div>
        </article>`;
    return new_message_html;
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

function getCookie(cname) {
    return document.cookie.split('; ').find((row) => row.startsWith(`${cname}=`))?.split('=')[1];
}

function initws() {
    // socket = new WebSocket(`ws://${window.location.host}/websocket_index`);
    socket = io.connect();
    // socket = io.connect(`https://${document.URL}`);
    document.getElementById('createpostform').onsubmit = (ev) => {
        ev.preventDefault();
        const msg = document.getElementById('createpostinput').value;
        document.getElementById('createpostinput').value = '';
        const username = document.getElementById('displayed_username').innerText;
        console.log(msg);
        // socket.send(JSON.stringify({'messageType': 'createpost', 'message': msg}));
        socket.emit('createpostrequest', {message: msg, auth_token: getCookie('auth_token'), username: username});
    }

    socket.on('createpostresponse', (data) => {
        console.log(data);
        currentChat = document.getElementById('chatbox').innerHTML
        document.getElementById('chatbox').innerHTML = newChat(data) + currentChat;
    })

    document.getElementById('')
    // const username = chatJSON.username;
    // const message = chatJSON.message;
    // const id = chatJSON.id;
    // const likes = chatJSON.likes;
}

function welcome() {
    // generateTestChats();  // Line is only here for tests
    if (ws) {
        updateChat();
        initws();
    } else {
        updateChat();
        setInterval(updateChat, 5000);
    }
}
