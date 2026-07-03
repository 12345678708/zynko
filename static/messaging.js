// messaging.js
const socket = io();
const username = (window.CURRENT_USER || document.querySelector('meta[name="username"]') && document.querySelector('meta[name="username"]').content) || prompt('Pseudo ?');

socket.emit('join', { username: username, room: 'global' });

socket.on('private_message', data => {
  const el = document.createElement('div');
  el.innerHTML = `<strong>DM from ${data.from || data.username}</strong>: ${data.body}`;
  document.getElementById('messages').appendChild(el);
  scrollMessages();
});

socket.on('group_message', data => {
  const el = document.createElement('div');
  el.innerHTML = `<em>Group ${data.group_id}</em> <strong>${data.username}</strong>: ${data.body}`;
  document.getElementById('messages').appendChild(el);
  scrollMessages();
});

socket.on('status', data => {
  const el = document.createElement('div');
  el.className = 'text-muted small';
  el.textContent = data.msg;
  document.getElementById('messages').appendChild(el);
  scrollMessages();
});

function scrollMessages(){
  const m = document.getElementById('messages');
  m.scrollTop = m.scrollHeight;
}

// DM form
const dmForm = document.getElementById('dmForm');
if(dmForm){
  dmForm.addEventListener('submit', e=>{
    e.preventDefault();
    const to = document.getElementById('dmTo').value.trim();
    const body = document.getElementById('dmBody').value.trim();
    if(!to || !body) return;
    socket.emit('private_message', { to, from: username, body });
    document.getElementById('dmBody').value = '';
  });
}

// Group form
const groupForm = document.getElementById('groupForm');
if(groupForm){
  groupForm.addEventListener('submit', e=>{
    e.preventDefault();
    const group_id = document.getElementById('groupId').value.trim();
    const body = document.getElementById('groupBody').value.trim();
    if(!group_id || !body) return;
    socket.emit('group_message', { group_id, username, body });
    document.getElementById('groupBody').value = '';
  });
}
