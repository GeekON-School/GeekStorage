

listOFLinks = [];

Dropzone.options.myAwesomeDropzone = {
        maxFilesize: 20, // Size in MB
        dictDefaultMessage: "Перенесите файлы сюда или кликните для загрузки",
        previewsContainer: false,
        removedfile: function (file) {
            var fileRef;
            return (fileRef = file.previewElement) != null ?
                fileRef.parentNode.removeChild(file.previewElement) : void 0;
        },

        success: function (file, response) {
            createZone();
            createCardLinkArea();

            createNewCard(response, file);
        },

        error: function (file, response) {
            alert(response);
        }

    };

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
 function createNewCard(response, file) {
     console.log(file);
     var img = document.createElement('img');
     img.className = 'card-img-left';
     img.height = 100;
     img.width = 100;
     img.align = 'left';
     img.src = file.dataURL;

     var icon = document.createElement('img');
     icon.className = 'tm-preview-link__icon';

     var valueLink = document.createElement('input');
     valueLink.value = response;
     valueLink.size = 100;

     var h = document.createElement("H5");
     h.align='center';
     var t = document.createTextNode("Прямая ссылка");
     h.appendChild(t);

     var insideDiv = document.createElement('div');
     //insideDiv.className = 'tm-preview-link tm-preview-link_markdown';
     //insideDiv.appendChild(icon);
     insideDiv.appendChild(h);
     insideDiv.appendChild(valueLink);
     var div = document.createElement('div');
     div.className = 'list-group-item';
     div.appendChild(img);
     div.appendChild(insideDiv);
     cardList = document.getElementById("cardList");
     cardList.appendChild(div);
 }

