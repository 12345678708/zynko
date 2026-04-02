let peer = new RTCPeerConnection();

async function startCall(){
    let stream = await navigator.mediaDevices.getUserMedia({video:true,audio:true});
    document.getElementById("local").srcObject = stream;

    stream.getTracks().forEach(track => peer.addTrack(track, stream));

    let offer = await peer.createOffer();
    await peer.setLocalDescription(offer);

    socket.emit("call", offer);
}

socket.on("call", async offer=>{
    await peer.setRemoteDescription(offer);

    let answer = await peer.createAnswer();
    await peer.setLocalDescription(answer);

    socket.emit("answer", answer);
});

socket.on("answer", async answer=>{
    await peer.setRemoteDescription(answer);
});
