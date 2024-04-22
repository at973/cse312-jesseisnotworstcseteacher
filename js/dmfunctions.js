console.log("TEST");
const socket = io();

socket.on('DMmessage', (data) => {
    console.log("MEssage:" + data);
});


function load() {
    const messageInput = document.getElementById("send-button");
    console.log("WORK:" + messageInput);
    messageInput.addEventListener("click", function(){
        let user = document.getElementById("user").value;
        let recipient = document.getElementById("recipient").value;
        let message = document.getElementById("DMmessage").value;
        socket.emit("createPostDM", message, recipient, user);
        console.log("HELLO TEST");
        document.getElementById("DMmessage").value = "";
    })
}
