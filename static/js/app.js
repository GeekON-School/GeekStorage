

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
     var data = JSON.parse(response);
     console.log(data);
     var img = document.createElement('img');
     img.className = 'card-img-left';
     img.id = 'img';
     img.height = 180;
     img.width = 240;
     img.align = 'left';
     img.src = file.dataURL;

     var directLink = document.createElement('input');
     directLink.value = data.direct_url;
     directLink.id = 'directLink';
     directLink.size = 85;

     var markdownLink = document.createElement('input');
     markdownLink.value = data.markdown;
     markdownLink.id = 'markdownLink';
     markdownLink.size = 85;

     var htmlLink= document.createElement('input');
     htmlLink.value = data.html;
     htmlLink.id = 'htmlLink';
     htmlLink.size = 85;

     var headerDirectUrl = document.createElement("H6");
     headerDirectUrl.align='center';
     var textNodeDirectLink = document.createTextNode("Прямая ссылка:");
     headerDirectUrl.appendChild(textNodeDirectLink);

     var headerMarkDownUrl = document.createElement("H6");
     headerMarkDownUrl.align='center';
     headerMarkDownUrl.id = 'headerMarkdownUrl';
     var textNodeMarkdownLink = document.createTextNode("Markdown");
     headerMarkDownUrl.appendChild(textNodeMarkdownLink);

     var headerHTMLUrl = document.createElement("H6");
     headerHTMLUrl.align='center';
     headerHTMLUrl.id = 'headerHTMLUrl';
     var textNodeHTMLLink = document.createTextNode("HTML");
     headerHTMLUrl.appendChild(textNodeHTMLLink);

     var insideDiv = document.createElement('div');
     insideDiv.appendChild(headerDirectUrl);
     insideDiv.appendChild(directLink);
     insideDiv.appendChild(headerMarkDownUrl);
     insideDiv.appendChild(markdownLink);
     insideDiv.appendChild(headerHTMLUrl);
     insideDiv.appendChild(htmlLink);
     var div = document.createElement('div');
     div.className = 'list-group-item';
     div.id = 'list-group-item';
     div.appendChild(img);
     div.appendChild(insideDiv);
     cardList = document.getElementById("cardList");
     cardList.appendChild(div);
 }

