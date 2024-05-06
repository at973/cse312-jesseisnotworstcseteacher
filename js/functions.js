const ws = true;
let socket = null;
let remain_timer = null;
function newChat(chatJSON) {
    const username = chatJSON.username;
    const message = chatJSON.message;
    const id = chatJSON.id;
    const likes = chatJSON.likes;
    const imageLink = chatJSON.image_link;
    console.log(chatJSON);
    const user2 = chatJSON.user2;
    const name = document.getElementById('name').innerHTML;
    let imageHTML = ""
    if(imageLink.length != 0){
        imageHTML = "<img src = /userUploads/" + imageLink + " width = \"400\">"
    }
  
    const new_message_html =
        `<article class="media">
            <div class="media-left" name="${username}">
                <p class="image is-64x64">
                    <img src="images/default-icon.png" />
                </p>
            </div>
            <div class="media-content">
                <div class="content">
                    <p> <strong> ${username} </strong> </p>
                    ${message}
                </div>
                <nav class="level">
                    <div class="level-left">
                        <div class="level-item">
                            <form action="/like" method="POST" enctype="application/x-www-form-urlencoded">
                                <input value = "${id}" type="hidden" name="id">
                                <button type="submit" value="Like" class="button is-ghost">
                                    <span class="icon-text">
                                        <span class="icon"><i class="fa-solid fa-thumbs-up"></i></span>
                                        <span> Like </span>
                                    </span>
                                </button>
                            </form>
                        </div>
                        <div class="level-item">
                            <label id="message_${id}">${likes}</label>
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
                <div class="cell">
                    <form action="/upload" method="POST" enctype="multipart/form-data">
                        <input value = "${id}" type="hidden" name="id">
                        <input value = "${name}" type="hidden" name="username">
                        <div class="file is-boxed cell">
                            <label class="file-label">
                                <input class="file-input" type="file" name="file" accept=".png, .jpg, .jpeg" />
                                <span class="file-cta">
                                    <span class="file-icon">
                                        <i class="fas fa-upload"></i>
                                    </span>
                                    <span class="file-label"> Choose a file… </span>
                                </span>
                            </label>
                        </div>
                        <div class="level-item" style="margin: 3px">
                            <button type="submit" class="button is-primary">Add photo to collection</button>
                        </div>
                    </form>
                </div>
            </div>
            <div id="${id}">
            ${imageHTML}<label>Posted by ${user2}</label>
            </div>
        </article>`;
    return new_message_html;
}

function clearChat() {
    document.getElementById("chatbox").innerHTML = "";
}

{
    var lengthOfMessage = 0; //This is such an ugly way to do this.
}

function updateChat() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            // clearChat();
            const messages = JSON.parse(this.response);
            console.log(lengthOfMessage)
            for(let j = 0; j < lengthOfMessage; j++){ //Remove messages that have already been displayed.
                messages.pop()
            }
            console.log(messages)
            if (Object.keys(messages).length > lengthOfMessage){
                lengthOfMessage = Object.keys(messages).length
            }
            console.log(lengthOfMessage)
            for (const message of messages) {
                document.getElementById("chatbox").innerHTML += newChat(message);
            }
        }
    }
    request.open("GET", "/messages");
    request.send();
}

function updateTimer() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const msg = JSON.parse(this.response)
            if (msg.time_remaining == 0) {
                document.getElementById('createpostsubmit').removeAttribute('disabled');
                clearTimeout(remain_timer);
            } else {
                document.getElementById('createpostsubmit').setAttribute('disabled', true);
            }
            document.getElementById('time_remaining').innerText = msg.time_remaining;
            console.log('time remaining', msg)
        }
    }
    request.open("GET", "/time_remaining");
    request.send();
}

function updateImage (id, imageLink, user2){
    console.log("TESTSTESTS");
    console.log(id,imageLink,user2);
    document.getElementById(id).innerHTML = "<img src = /userUploads/" + imageLink + " width = \"400\"><label>Posted by " + user2 + "</label>";
}

function updatePFP(image_link, user) {
    console.log("GET HERE")
    const elements = document.getElementsByName(user);
    for (let i = 0; i < elements.length; i++) {
        elements[i].innerHTML = `
            <p class="image is-64x64">
                <img src="/PFPUploads/${image_link}" alt="Profile Picture" />
            </p>
        `;
    }
}

function updateLikes (id, likes){
    document.getElementById("message_" + id).innerHTML = likes;
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
    socket = io.connect(null, {rememberTransport: false});
    // socket = io.connect(`https://${document.URL}`);
    document.getElementById('createpostform').onsubmit = (ev) => {
        ev.preventDefault();
        console.log('createpostform executed')
        const msg = document.getElementById('createpostinput').value;
        document.getElementById('createpostinput').value = '';
        const username = document.getElementById('displayed_username').innerText;
        const delay = document.getElementById('delaypostinput').value;
        document.getElementById('delaypostinput').value = '';
        const delay_unit = document.getElementById('delaypostunit').value;
        console.log(msg);
        // socket.send(JSON.stringify({'messageType': 'createpost', 'message': msg}));
        socket.emit('createpostrequest', {message: msg, 
            auth_token: getCookie('auth_token'), username: username, 
            delay: delay, delay_unit: delay_unit});
    }

    socket.on('createpostresponse', (data) => {
        console.log(data);
        currentChat = document.getElementById('chatbox').innerHTML
        document.getElementById('chatbox').innerHTML = newChat(data) + currentChat;
    })

    socket.on('updatePost', (data) => {
        console.log(data);
        console.log("print properly");
        updateImage(data.id,data.image_link,data.username);
    })

    socket.on('updateProfilePicture', (data) => {
        console.log(data.image_link);
        console.log("Here test");
        updatePFP(data.image_link,data.username);
    })

    socket.on('updateLikes', (data) => {
        console.log(data);
        updateLikes(data.id,data.likes);
    })

    socket.on('timeremainingid', (data) => {
        id = data.id;
        document.cookie = 'time_remaining_id' + '=; Max-Age=0'
        document.cookie = `time_remaining_id=${id};`
        remain_timer = setInterval(updateTimer, 1000);
    })
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
