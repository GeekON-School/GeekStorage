

listOFLinks = [];

Dropzone.options.myAwesomeDropzone = {
        maxFilesize: 20, // Size in MB
        dictDefaultMessage: "Перенесите файлы сюда",
        previewsContainer:
        removedfile: function (file) {
            var fileRef;
            return (fileRef = file.previewElement) != null ?
                fileRef.parentNode.removeChild(file.previewElement) : void 0;
        },

        success: function (file, response) {
            createZone();
            createCardLinkArea();

            createNewCard(response);
        },

        error: function (file, response) {
            alert(response);
        }

    };

/*function addToListAndPrint(response) {
    var newLI = document.createElement("li");
    displaySpellList = document.getElementById("listOfLinks");
    newContent = document.createTextNode(response);
    newLI.appendChild(newContent);
    displaySpellList.appendChild(newLI);

}*/
function createZone() {
    console.log(1);
    var div =  document.createElement('div');
    div.className = 'card';
    div.id = 'cardZone';
    cardZone = document.getElementById("cards");
    cardZone.appendChild(div);
    
}
function createCardLinkArea() {
   
     var div = document.createElement('div');
     div.className = 'list-group list-group-flush';
     div.id = "cardList";
     cardLinks = document.getElementById("cardZone");
     cardLinks.appendChild(div);

}
 function createNewCard(response) {
     //var a1 = "<div class=\"card\"> <div class=\"card-body\"> <div class=\"card-title\"> Карточка  </div> </div></div>";
     //document.getElementById("cardList").innerHTML = a1;
     var div = document.createElement('div');
     div.className = 'list-group-item';
     div.innerHTML = response;
     cardList = document.getElementById("cardList");
     cardList.appendChild(div);
 }

