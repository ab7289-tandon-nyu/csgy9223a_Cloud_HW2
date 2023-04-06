
window.SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition

function voiceSearch() {
    if ('SpeechRecognition' in window) {
        console.log("SpeechRecognition is Working");
    } else {
        console.log("SpeechRecognition is Not Working");
    }

    var inputSearchQuery = document.getElementById("search_query");
    const recognition = new window.SpeechRecognition();


    micButton = document.getElementById("mic_search");

    if (micButton.innerHTML == "mic") {
        recognition.start();
    } else if (micButton.innerHTML == "mic_off") {
        recognition.stop();
    }

    recognition.addEventListener("start", function () {
        micButton.innerHTML = "mic_off";
        console.log("Recording.....");
    });

    recognition.addEventListener("end", function () {
        console.log("Stopping recording.");
        micButton.innerHTML = "mic";
    });

    recognition.addEventListener("result", resultOfSpeechRecognition);
    function resultOfSpeechRecognition(event) {
        const current = event.resultIndex;
        transcript = event.results[current][0].transcript;
        inputSearchQuery.value = transcript;
        console.log("transcript : ", transcript)
    }
}




function textSearch() {
    var searchText = document.getElementById('search_query');
    if (!searchText.value) {
        alert('Please enter a valid text or voice input!');
    } else {
        searchText = searchText.value.trim().toLowerCase();
        console.log('Searching Photos....');
        searchPhotos(searchText);
    }

}


function searchPhotos(searchText) {

    console.log(searchText);
    document.getElementById('search_query').value = searchText;
    document.getElementById('photos_search_results').innerHTML = "<h4 style=\"text-align:center\">";

    var params = {
        'q': searchText
    };
    // params = { ...params, ...getApiAuth() };

    apigClient.searchGet(params, {}, {})
        .then(function (result) {
            console.log("Result : ", JSON.stringify(result));

            image_paths = result["data"];
            console.log("image_paths : ", JSON.stringify(image_paths));

            var photosDiv = document.getElementById("photos_search_results");
            photosDiv.innerHTML = "";

            var n;
            for (n = 0; n < image_paths.length; n++) {
                // images_list = image_paths[n].split('/');
                // imageName = images_list[images_list.length - 1];
                const imageObj = image_paths[n];

                photosDiv.innerHTML += `<figure><img src="${imageObj.url}" style="width:25%"><figcaption></figcaption></figure>`;
            }

        }).catch(function (result) {
            var photosDiv = document.getElementById("photos_search_results");
            photosDiv.innerHTML = "Image not found";
            console.log(result);
        });
}

function getBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            let encoded = reader.result.replace(/^data:(.*;base64,)?/, '');
            if (encoded.length % 4 > 0) {
                encoded += '='.repeat(4 - (encoded.length % 4));
            }
            resolve(encoded);
        };
        reader.onerror = (error) => reject(error);
    });
}

function uploadPhoto() {
    /*let file = document.getElementById('uploaded_file').files[0];
    let fileName = file.name;
    let file_type = file.type;
    let reader = new FileReader();
    reader.onload = function() {
        let arrayBuffer = this.result;
        let blob = new Blob([new Int8Array(arrayBuffer)], {
            type: file_type
        });
        let blobUrl = URL.createObjectURL(blob);
        let data = document.getElementById('uploaded_file').files[0];
        let xhr = new XMLHttpRequest();
        xhr.withCredentials = true;
        xhr.addEventListener("readystatechange", function () {
            if (this.readyState === 4) {
                console.log(this.responseText);
                //document.getElementById('uploadText').innerHTML ='Image Uploaded  !!!';
                //document.getElementById('uploadText').style.display = 'block';
            }
        });
        xhr.withCredentials = false;
        xhr.open("PUT", "https://3gfggbrwob.execute-api.us-east-1.amazonaws.com/prod/imagesbucket/"+data.name);
        xhr.setRequestHeader("Content-Type", data.type);
       
        xhr.setRequestHeader("x-amz-meta-customLabels", custom_labels.value);
       
        xhr.send(file);
    };
    reader.readAsArrayBuffer(file);
    */
    var filePath = (document.getElementById('uploaded_file').value).split("\\");
    var fileName = filePath[filePath.length - 1];

    let customLabels;
    if (document.getElementById('custom_labels').value !== "") {
        customLabels = document.getElementById('custom_labels').value;
    }
    console.log(fileName);
    console.log(customLabels);

    var reader = new FileReader();
    var file = document.getElementById('uploaded_file').files[0];
    console.log('File : ', file);
    document.getElementById('uploaded_file').value = "";

    if ((filePath == "") || (!['png', 'jpg', 'jpeg'].includes(fileName.split(".")[1]))) {
        alert("Please upload a valid .png/.jpg/.jpeg file!");
    } else {

        var params = {
            //headers: {
            'item': file.name,
            'Content-Type': file.type,
            'x-amz-meta-customLabels': customLabels
            //}
        };
        // params = { ...params, ...getApiAuth() };
        var additionalParams = {};

        reader.onload = function (event) {
            body = btoa(event.target.result);
            console.log('Reader body : ', body);
            return apigClient.uploadItemPut(params, body, additionalParams)
                .then(function (result) {
                    console.log(result);
                })
                .catch(function (error) {
                    console.log(error);
                })
        }
        reader.readAsBinaryString(file);
    }

}