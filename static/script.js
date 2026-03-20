const socket = io();

function send() {

    let msg = document.getElementById("msg").value;
    let file = document.getElementById("file").files[0];

    if (file) {

        let formData = new FormData();
        formData.append("file", file);

        fetch("/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {

            socket.emit("send_message", {
                text: msg,
                image: data.url
            });

        });

    } else {

        socket.emit("send_message", {
            text: msg
        });

    }

    document.getElementById("msg").value = "";
}

socket.on("receive_message", function(data) {

    let div = document.createElement("div");

    if (data.image) {
        div.innerHTML = `<p>${data.text}</p><img src="${data.image}" width="150">`;
    } else {
        div.innerText = data.text;
    }

    document.getElementById("messages").appendChild(div);
});
