async function sendMessage() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (text === "") return;
  
    // Get chat history (you might maintain this in your frontend)
    const chatHistory = []; // Replace with your current history, if applicable
    const modelSelect = document.getElementById('modelSelect');
    const selectedModel = modelSelect.value;
  
    // Append the user's message to the chat interface
    appendMessage('user', text);
  
    // Prepare the data payload
    const payload = {
      prompt: text,
      history: chatHistory,
      model: selectedModel
    };
  
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (data.response) {
        appendMessage('bot', data.response);
        // Optionally update your chat history with data.history
      } else if (data.error) {
        appendMessage('bot', 'Error: ' + data.error);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      appendMessage('bot', 'Error connecting to server.');
    }
  
    // Clear input field
    input.value = "";
  }
  
  function appendMessage(sender, text) {
    const chatBody = document.getElementById('chatBody');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    const messageParagraph = document.createElement('p');
    messageParagraph.textContent = text;
    messageDiv.appendChild(messageParagraph);
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
  }


  document.getElementById('sendApiBtn').addEventListener('click', function() {
    const apiKey = document.getElementById('chatInput').value;
    fetch('/set_api_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ apiKey: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('API Key set successfully');
            window.location.href = data.redirect; // Redirect to the index page
        } else {
            alert('Failed to set API Key');
        }
    })
    .catch(error => console.error('Error:', error));
});