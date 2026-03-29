let pc = new RTCPeerConnection()

async function startCall(){
    let stream = await navigator.mediaDevices.getUserMedia({video:true,audio:true})
    stream.getTracks().forEach(t=>pc.addTrack(t, stream))
}
