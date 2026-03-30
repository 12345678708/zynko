let socket = io();
let user = prompt("Ton pseudo");

socket.emit("join", {user:user});

// ===== ENVOI TEXTE =====
function send(){
    let msg = document.getElementById("msg").value;

    socket.emit("message", {
        user:user,
        text:msg
    });

    document.getElementById("msg").value="";
}

// ===== AFFICHAGE =====
socket.on("message", data=>{
    let div = document.createElement("div");
    div.className = "msg";

    if(data.user === user) div.classList.add("me");

    if(data.text){
        div.innerText = data.user + " : " + data.text;
    }

    if(data.image){
        div.innerHTML = `<b>${data.user}</b><br><img src="/static/uploads/${data.image}" width="150">`;
    }

    if(data.audio){
        div.innerHTML = `<b>${data.user}</b><br><audio controls src="${data.audio}"></audio>`;
    }

    document.getElementById("chat").appendChild(div);
});

// ===== IMAGE =====
function sendImage(){
    let file = document.getElementById("img").files[0];

    let formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
        method:"POST",
        body:formData
    })
    .then(res=>res.json())
    .then(data=>{
        socket.emit("message", {
            user:user,
            image:data.file
        });
    });
}

// ===== VOCAL =====
let mediaRecorder;
let audioChunks = [];

async function startRecording(){
    let stream = await navigator.mediaDevices.getUserMedia({audio:true});
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e=>{
        audioChunks.push(e.data);
    };

    mediaRecorder.onstop = ()=>{
        let blob = new Blob(audioChunks, {type:"audio/webm"});
        let url = URL.createObjectURL(blob);

        socket.emit("message", {
            user:user,
            audio:url
        });

        audioChunks = [];
    };

    mediaRecorder.start();
}

function stopRecording(){
    mediaRecorder.stop();
}
