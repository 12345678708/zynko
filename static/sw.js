self.addEventListener("push", e=>{
    let data = e.data.json();

    self.registration.showNotification(data.title,{
        body:data.body
    });
});
