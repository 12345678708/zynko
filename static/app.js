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

    if(data.audio){
        div.innerHTML = `<audio controls src="/static/uploads/${data.audio}"></audio>`;
    }

    document.getElementById("chat").appendChild(div);
});

// ===== IMAGE =====
function sendImage(){
    let file = document.getElementById("img").files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/upload", {method:"POST", body:form})
    .then(r=>r.json())
    .then(d=>{
        socket.emit("send_message", {
            user:user,
            image:d.file
        });
    });
}

// ===== AUDIO =====
let recorder;
async function startAudio(){
    let stream = await navigator.mediaDevices.getUserMedia({audio:true});
    recorder = new MediaRecorder(stream);
    recorder.start();

    recorder.ondataavailable = async e=>{
        let blob = e.data;

        let form = new FormData();
        form.append("audio", blob, "audio.webm");

        let res = await fetch("/upload_audio", {method:"POST", body:form});
        let data = await res.json();

        socket.emit("send_message", {
            user:user,
            audio:data.audio
        });
    };
}

function stopAudio(){
    recorder.stop();
}

// ===== TYPING =====
function typing(){
    socket.emit("typing", {user:user});
}

function stopTyping(){
    socket.emit("stop_typing", {user:user});
}

// ===== NOTIFICATION =====
if("Notification" in window){
    Notification.requestPermission();
}
