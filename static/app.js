let socket = io();
let user = "User" + Math.floor(Math.random()*1000);

socket.emit("connect_user", {user:user});

// ===== MESSAGE =====
function send(){
    let txt = document.getElementById("msg").value;

    socket.emit("send_message", {
        user:user,
        text:txt
    });

    document.getElementById("msg").value="";
}

// ===== RECEIVE =====
socket.on("new_message", data=>{
    let div = document.createElement("div");
    div.className = "msg";

    if(data.user === user) div.classList.add("me");

    if(data.text){
        div.innerText = data.user + ": " + data.text;
    }

    if(data.image){
        div.innerHTML = `<img src="/static/uploads/${data.image}" width="150">`;
    }

    document.getElementById("chat").appendChild(div);
});

// ===== TYPING =====
function typing(){
    socket.emit("typing", {user:user});
}

function stopTyping(){
    socket.emit("stop_typing", {user:user});
}

// ===== IMAGE =====
function sendImage(){
    let file = document.getElementById("img").files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/upload", {
        method:"POST",
        body:form
    })
    .then(r=>r.json())
    .then(d=>{
        socket.emit("send_message", {
            user:user,
            image:d.file
        });
    });
}
