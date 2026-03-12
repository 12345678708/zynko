const socket = io()

function sendMessage(){

let msg = document.getElementById("msg").value
let receiver = document.getElementById("receiver").value

socket.emit("send_message",{
receiver:receiver,
message:msg
})

document.getElementById("msg").value=""
}

socket.on("receive_message", function(data){

let box=document.getElementById("messages")

let div=document.createElement("div")

div.className="bubble"

div.innerText=data.sender+" : "+data.message

box.appendChild(div)

})
