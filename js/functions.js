function newChat(chatJSON) {
    const username = chatJSON.username;
    const message = chatJSON.message;
    const id = chatJSON.id;
    const likes = chatJSON.likes;
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
                    <form action="/upload" method="POST" enctype="multipart/form-data">
                        <div class="level-item">
                            <div class="file">
                                <label class="file-label">
                                    <input class="file-input" type="file" name="file" />
                                    <span class="file-icon">
                                        <i class="fas fa-upload"></i>
                                    </span>
                                </label>
                            </div>
                        </div>
                        <div class="level-item" style="margin: 3px">
                            <button type="submit" class="button is-primary">Add photo to collection</button>
                        </div>
                    </form>
                    </div>
                </nav>
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

function welcome() {
    // generateTestChats();  // Line is only here for tests
    updateChat();
    setInterval(updateChat, 5000);
}
