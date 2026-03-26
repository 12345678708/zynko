var socket = io();

let currentUser = null;

function selectUser(user){
    currentUser = user;
    document.getElementById("chatWith").innerText = user;
    document.getElementById("messages").innerHTML = "";
}

function send(){
    let input = document.getElementById("msg");
    let text = input.value;

    if(!text || !currentUser) return;

    socket.emit("send_message", {
        text: text,
        to: currentUser
    });

    input.value="";
}

function handleKey(e){
    if(e.key === "Enter"){
        send();
    }
}

socket.on("new_message", function(data){

    if(data.to !== currentUser) return;

    let box = document.getElementById("messages");

    let div = document.createElement("div");
    div.className = "msg";

    if(data.me){
        div.classList.add("me");
    }

    div.innerText = data.text;

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
});
