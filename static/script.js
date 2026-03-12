let currentFriend=null

function openChat(friend){

currentFriend=friend

loadMessages()

setInterval(loadMessages,2000)

}

function loadMessages(){

if(!currentFriend)return

fetch("/messages/"+currentFriend)

.then(r=>r.json())

.then(data=>{

let box=document.getElementById("messages")

box.innerHTML=""

data.forEach(m=>{

let div=document.createElement("div")

div.className="bubble"

div.innerText=m[0]+" : "+m[1]

box.appendChild(div)

})

})

}
