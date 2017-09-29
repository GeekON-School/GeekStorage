

listOFLinks = [];

Dropzone.options.myAwesomeDropzone = {
        maxFilesize: 20, // Size in MB
        dictDefaultMessage: "Перенесите файлы сюда",
        removedfile: function (file) {
            var fileRef;
            return (fileRef = file.previewElement) != null ?
                fileRef.parentNode.removeChild(file.previewElement) : void 0;
        },

        success: function (file, response) {
            document.getElementById("links").innerHTML = "Ссылки";
            addToListAndPrint(response);
        },

        error: function (file, response) {
            alert(response);
        }

    };

function addToListAndPrint(response) {
    var newLI = document.createElement("li");
    displaySpellList = document.getElementById("listOfLinks");
    newContent = document.createTextNode(response);
    newLI.appendChild(newContent);
    displaySpellList.appendChild(newLI);

}
 function createNewCard(response) {
     
 }

