let socket = io();

let user = prompt("Pseudo");

socket.emit("join", {user:user});

function send(){
    let msg = document.getElementById("msg").value;

    socket.emit("message", {
        user:user,
        text:msg
    });

    document.getElementById("msg").value="";
}

socket.on("message", data=>{
    let div = document.createElement("div");
    div.className = "msg";

    if(data.user === user) div.classList.add("me");

    div.innerText = data.user + " : " + data.text;

    document.getElementById("chat").appendChild(div);
});
