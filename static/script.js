const messages=document.getElementById("messages");
const msgInput=document.getElementById("msg");
const fileInput=document.getElementById("file");
let mediaRecorder;
let audioChunks=[];

// ENVOI MESSAGE
function send(){
let text=msgInput.value;
let file=fileInput.files[0];
if(file){
let formData=new FormData();
formData.append("file",file);
fetch("/upload",{method:"POST",body:formData})
.then(r=>r.json()).then(data=>{
socket.emit("send_message",{user:USER,text:text,image:data.file});
});
}else{
socket.emit("send_message",{user:USER,text:text});
}
msgInput.value="";
fileInput.value="";
}

// RECEIVE
socket.on("new_message",data=>{
let div=document.createElement("div");
div.className="msg "+(data.user===USER?"me":"other");
if(data.text) div.innerHTML+=data.text;
if(data.image) div.innerHTML+=`<br><img src="/static/uploads/${data.image}" width=150>`;
if(data.audio) div.innerHTML+=`<br><audio controls src="/static/uploads/${data.audio}"></audio>`;
messages.appendChild(div);
messages.scrollTop=999999;
if(data.user!==USER && Notification.permission==="granted"){
new Notification(data.user+": "+(data.text||"📷 Image"));
}
});

// Notifications
if(Notification.permission!=="granted") Notification.requestPermission();

// AUDIO RECORD
function record(){
navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{
mediaRecorder=new MediaRecorder(stream);
mediaRecorder.start();
mediaRecorder.ondataavailable=e=>audioChunks.push(e.data);
mediaRecorder.onstop=()=>{
let blob=new Blob(audioChunks);
audioChunks=[];
let file=new File([blob],"audio.webm");
let formData=new FormData();
formData.append("file",file);
fetch("/upload",{method:"POST",body:formData}).then(r=>r.json()).then(data=>{
socket.emit("send_message",{user:USER,audio:data.file});
});
};
setTimeout(()=>mediaRecorder.stop(),3000);
});
}

// DARK MODE
function toggleDark(){document.body.classList.toggle("dark");}
