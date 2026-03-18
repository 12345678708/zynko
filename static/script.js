const chat=document.getElementById("chat");

function send(){
let text=document.getElementById("msg").value;
let target=document.getElementById("target").value;

socket.emit("send_message",{
sender:USER,
receiver:target,
text:text
});
}

socket.on("new_message",data=>{
let div=document.createElement("div");
div.className="msg "+(data.sender===USER?"me":"other");
div.innerText=data.sender+" : "+data.text;
chat.appendChild(div);
});
