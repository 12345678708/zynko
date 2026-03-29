let stream;

async function startAudio(){
    stream = await navigator.mediaDevices.getUserMedia({audio:true})
}

async function startVideo(){
    stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true})
}
