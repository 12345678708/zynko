const socket = io();

let room = null;

function newGroup(){
    let name = prompt("Nom du groupe");

    fetch("/create_group",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name:name})
    });

    addRoom(name);
}

function addRoom(name){
    let div = document.createElement("div");
    div.innerText = name;
    div.onclick = () => joinRoom(name);
    document.getElementById("rooms").appendChild(div);
}

function joinRoom(name){
    room = name;
    document.getElementById("header").innerText = name;
    socket.emit("join",{room:name});
}

function send(){
    let msg = document.getElementById("msg").value;

    socket.emit("send",{
        room:room,
        text:msg
    });

    document.getElementById("msg").value="";
}

socket.on("msg",(data)=>{
    let div = document.createElement("div");
    div.className="bubble";
    div.innerText=data.text;

    document.getElementById("messages").appendChild(div);
});
