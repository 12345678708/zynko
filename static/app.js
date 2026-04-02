const socket = io();
let username = prompt("Pseudo ?");

socket.emit("join", {username});

// ================= MESSAGE
function send(){
    let input = document.getElementById("msg");
    socket.emit("message", {
        user: username,
        text: input.value
    });
    input.value="";
}

// ================= RECEVOIR
socket.on("message", data=>{
    let div = document.createElement("div");
    div.className="msg";
    div.innerHTML = "<b>"+data.user+"</b>: "+data.text;
    document.getElementById("messages").appendChild(div);
});

// ================= USER COUNT
socket.on("user_count", n=>{
    document.getElementById("users").innerText="👥 "+n;
});

// ================= TYPING
document.getElementById("msg").addEventListener("input", ()=>{
    socket.emit("typing", username);
});

socket.on("typing", user=>{
    document.getElementById("typing").innerText = user+" écrit...";
});

// ================= VOCAUX
let mediaRecorder;
let audioChunks=[];

function startRecording(){
    navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.start();

        mediaRecorder.ondataavailable = e=>{
            audioChunks.push(e.data);
        };

        mediaRecorder.onstop = ()=>{
            let blob = new Blob(audioChunks);
            let form = new FormData();
            form.append("file", blob, "audio.webm");

            fetch("/upload", {method:"POST", body:form})
            .then(r=>r.json())
            .then(res=>{
                socket.emit("message", {
                    user: username,
                    text: `<audio controls src="${res.url}"></audio>`
                });
            });

            audioChunks=[];
        };

        setTimeout(()=>mediaRecorder.stop(), 3000);
    });
}

// ================= IMAGE
function sendImage(){
    let input = document.createElement("input");
    input.type="file";

    input.onchange = ()=>{
        let file = input.files[0];
        let form = new FormData();
        form.append("file", file);

        fetch("/upload", {method:"POST", body:form})
        .then(r=>r.json())
        .then(res=>{
            socket.emit("message", {
                user: username,
                text: `<img src="${res.url}" width="200">`
            });
        });
    };

    input.click();
}
