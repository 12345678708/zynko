const chat=document.getElementById("chat");

function send(){
let text=document.getElementById("msg").value;

socket.emit("send_message",{
sender:USER,
receiver:"global",
text:text
});
}

socket.on("new_message",data=>{
let div=document.createElement("div");
div.className="msg "+(data.sender===USER?"me":"other");

div.innerHTML = data.text + 
` <span onclick="react('${data.text}','❤️')">❤️</span>`;

chat.appendChild(div);
});

// ❤️ reaction
function react(msg,emoji){
socket.emit("react",{msg,emoji,user:USER});
}

socket.on("reaction",data=>{
console.log("reaction",data);
});

// 📞 CALL
function call(){
socket.emit("call",{from:USER});
}

socket.on("incoming_call",data=>{
alert("📞 Appel de "+data.from);
});

// 🌙
function toggleDark(){
document.body.classList.toggle("dark");
}
