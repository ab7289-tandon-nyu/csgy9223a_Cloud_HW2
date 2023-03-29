var checkout = {};

$(document).ready(function() {
  var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

  $(window).load(function() {
    $messages.mCustomScrollbar();
    insertResponseMessage('Hi there, I\'m your personal Concierge. How can I help?');
  });

  function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar('scrollTo', 'bottom', {
      scrollInertia: 10,
      timeout: 0
    });
  }

  function setDate() {
    d = new Date()
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ':' + m + '</div>').appendTo($('.message:last'));
    }
  }

  function callChatbotApi(message) {
    // params, body, additionalParams
    return sdk.chatbotPost({}, {
      messages: [{
        type: 'unstructured',
        unstructured: {
          text: message
        }
      }]
    }, {});
  }

  function insertMessage() {
    msg = $('.message-input').val();
    if ($.trim(msg) == '') {
      return false;
    }
    $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
    setDate();
    $('.message-input').val(null);
    updateScrollbar();

    callChatbotApi(msg)
      .then((response) => {
        console.log(response);
        var data = response.data;

        if (data.messages && data.messages.length > 0) {
          console.log('received ' + data.messages.length + ' messages');

          var messages = data.messages;

          for (var message of messages) {
            if (message.type === 'unstructured') {
              insertResponseMessage(message.unstructured.text);
            } else if (message.type === 'structured' && message.structured.type === 'product') {
              var html = '';

              insertResponseMessage(message.structured.text);

              setTimeout(function() {
                html = '<img src="' + message.structured.payload.imageUrl + '" witdth="200" height="240" class="thumbnail" /><b>' +
                  message.structured.payload.name + '<br>$' +
                  message.structured.payload.price +
                  '</b><br><a href="#" onclick="' + message.structured.payload.clickAction + '()">' +
                  message.structured.payload.buttonLabel + '</a>';
                insertResponseMessage(html);
              }, 1100);
            } else {
              console.log('not implemented');
            }
          }
        } else {
          insertResponseMessage('Oops, something went wrong. Please try again.');
        }
      })
      .catch((error) => {
        console.log('an error occurred', error);
        insertResponseMessage('Oops, something went wrong. Please try again.');
      });
  }

  $('.message-submit').click(function() {
    insertMessage();
  });

  $(window).on('keydown', function(e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  })

  function insertResponseMessage(content) {
    $('<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    setTimeout(function() {
      $('.message.loading').remove();
      $('<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' + content + '</div>').appendTo($('.mCSB_container')).addClass('new');
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }

});


let queuedImagesArray = [],
    savedForm = document.querySelector("#saved-form"),
    queuedForm = document.querySelector("#queued-form"),
    savedDiv = document.querySelector('.saved-div'),
    queuedDiv = document.querySelector('.queued-div'),
    inputDiv = document.querySelector('.input-div'),
    input = document.querySelector('.input-div input'),
    serverMessage = document.querySelector('.server-message'),
    images="",//let images = "";
    savedImages = JSON.parse(JSON.stringify(images)),
    deleteImages = [];

    // SAVED IMAGES
    if(savedImages){
      displaySavedImages()
    } 

    function displaySavedImages(){
      let images = "";
        savedImages.forEach((image, index) => {
          images += `<div class="image">
                      <img src="http://localhost:3000/${image.image_key}" alt="image">
                      <span onclick="deleteSavedImage(${index})">&times;</span>
                    </div>`;
        })
      savedDiv.innerHTML = images;
    }

    function deleteSavedImage(index) {
      deleteImages.push(savedImages[index].image_key)
      savedImages.splice(index, 1);
      displaySavedImages();
    }

    savedForm.addEventListener("submit", (e) => {
      e.preventDefault()
      deleteImagesFromServer()
    });

    function deleteImagesFromServer() {

      fetch("delete", {
        method: "PUT",
        headers: {
          "Accept": "application/json, text/plain, */*",
          "Content-type": "application/json"
        },
        body: JSON.stringify({deleteImages})
      })

      .then(response => {
        if (response.status !== 200) throw Error(response.statusText)
        deleteImages = []
        serverMessage.innerHTML = response.statusText
        serverMessage.style.cssText = "background-color: #d4edda; color:#1b5e20"
      })

      .catch(error => {
        serverMessage.innerHTML = error
        serverMessage.style.cssText = "background-color: #f8d7da; color:#b71c1c"
      });

    }

    // QUEUED IMAGES

    function displayQueuedImages() {
      
      queuedImagesArray.forEach((image, index) => {
        images += `<div class="image">
                    <img src="${URL.createObjectURL(image)}" alt="image">
                    <span onclick="deleteQueuedImage(${index})">&times;</span>
                  </div>`;
      })
      queuedDiv.innerHTML = images;
    }

    function deleteQueuedImage(index) {
      queuedImagesArray.splice(index, 1);
      displayQueuedImages();
    }

    input.addEventListener("change", () => {
      const files = input.files;
      for (let i = 0; i < files.length; i++) {
        queuedImagesArray.push(files[i])
      }
      queuedForm.reset();
      displayQueuedImages()
    })

    inputDiv.addEventListener("drop", (e) => {
      e.preventDefault()
      const files = e.dataTransfer.files
      for (let i = 0; i < files.length; i++) {
        if (!files[i].type.match("image")) continue; // only photos
        
        if (queuedImagesArray.every(image => image.name !== files[i].name))
          queuedImagesArray.push(files[i])
      }
      displayQueuedImages()
    })

    queuedForm.addEventListener("submit", (e) => {
      e.preventDefault()
      sendQueuedImagesToServer()
    });

    function sendQueuedImagesToServer() {
      const formData = new FormData(queuedForm);

      queuedImagesArray.forEach((image, index) => {
        formData.append(`file[${index}]`, image)
      })

      fetch("upload", {
        method: "POST",
        body: formData
      })
        
      .then(response => {
        if(response.status !== 200) throw Error(response.statusText)
        location.reload() 
      })

      .catch( error => { 
        serverMessage.innerHTML = error
        serverMessage.style.cssText = "background-color: #f8d7da; color:#b71c1c"
      });

    }