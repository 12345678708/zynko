let recorder, audioChunks

async function record(){
    let stream = await navigator.mediaDevices.getUserMedia({audio:true})
    recorder = new MediaRecorder(stream)

    recorder.ondataavailable = e => audioChunks.push(e.data)

    recorder.onstop = ()=>{
        let blob = new Blob(audioChunks)
        let reader = new FileReader()
        reader.onload = ()=>{
            socket.emit("voice",{user:"me",audio:reader.result})
        }
        reader.readAsDataURL(blob)
    }

    audioChunks = []
    recorder.start()

    setTimeout(()=>recorder.stop(), 3000)
}
