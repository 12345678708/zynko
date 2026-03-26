const socket = io();
let room = null;

// NOTIFICATIONS
if(Notification.permission !== "granted"){
    Notification.requestPermission();
}

function notify(text){
    if(Notification.permission==="granted"){
        new Notification("Zynko",{body:text});
    }
}

// ROOMS
function createRoom(){
    let name=prompt("Nom");
    if(!name) return;

    let div=document.createElement("div");
    div.innerText=name;
    div.onclick=()=>joinRoom(name);

    document.getElementById("rooms").appendChild(div);
}

function joinRoom(name){
    room=name;
    document.getElementById("header").innerText=name;
    socket.emit("join",{room:name});
}

// SEND
function send(){

    let msg=document.getElementById("msg").value;
    let file=document.getElementById("file").files[0];

    if(file){
        let form=new FormData();
        form.append("file",file);

        fetch("/upload",{method:"POST",body:form})
        .then(r=>r.json())
        .then(data=>{
            socket.emit("send",{room:room,image:data.url});
        });
    }

    if(msg){
        socket.emit("send",{room:room,text:msg});
    }

    document.getElementById("msg").value="";
}

// RECEIVE
socket.on("msg",(data)=>{

    let div=document.createElement("div");
    div.className="bubble";

    if(data.text){
        div.innerText=data.text;
    }

    if(data.image){
        let img=document.createElement("img");
        img.src=data.image;
        img.style.maxWidth="200px";
        div.appendChild(img);
    }

    document.getElementById("messages").appendChild(div);

    notify(data.text || "Image reçue");
});

// AUDIO
function record(){
    navigator.mediaDevices.getUserMedia({audio:true})
    .then(stream=>{
        const recorder=new MediaRecorder(stream);
        let chunks=[];

        recorder.ondataavailable=e=>chunks.push(e.data);

        recorder.onstop=()=>{
            let blob=new Blob(chunks);
            let url=URL.createObjectURL(blob);

            let audio=document.createElement("audio");
            audio.src=url;
            audio.controls=true;

            document.getElementById("messages").appendChild(audio);
        };

        recorder.start();

        setTimeout(()=>recorder.stop(),3000);
    });
}
