import 'bootstrap/dist/css/bootstrap.min.css';
import 'dropzone/dist/dropzone.css';
import '../static/css/app.css';
import Dropzone from 'dropzone';

Dropzone.autoDiscover = false;

var currentPage = 1;
var perPage = 25;

Dropzone.options.myAwesomeDropzone = {
    maxFilesize: 200,
    dictDefaultMessage: 'Перенесите файлы сюда или кликните для загрузки',
    previewsContainer: false,

    removedfile: function (file) {
        var fileRef;
        return (fileRef = file.previewElement) != null ?
            fileRef.parentNode.removeChild(file.previewElement) : void 0;
    },

    success: function () {
        loadFiles(1);
    },

    error: function (file, response) {
        if (response && response.error) {
            alert(response.error);
        } else {
            alert(response);
        }
    }
};

function formatDate(value) {
    if (!value) {
        return '';
    }
    return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(value));
}

function fileSize(size) {
    if (!size && size !== 0) {
        return '';
    }
    if (size < 1024) {
        return size + ' B';
    }
    if (size < 1024 * 1024) {
        return Math.round(size / 102.4) / 10 + ' KB';
    }
    return Math.round(size / 1024 / 102.4) / 10 + ' MB';
}

function setEmptyRow(message) {
    var tableBody = document.getElementById('filesTableBody');
    tableBody.innerHTML = '';
    var row = document.createElement('tr');
    row.className = 'empty-row';
    var cell = document.createElement('td');
    cell.colSpan = 5;
    cell.className = 'text-center text-muted py-4';
    cell.innerText = message;
    row.appendChild(cell);
    tableBody.appendChild(row);
}

function copyText(text, button) {
    var originalText = button.innerText;
    var done = function () {
        button.innerText = 'Скопировано';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-success');
        setTimeout(function () {
            button.innerText = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-primary');
        }, 1400);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done);
        return;
    }

    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    done();
}

function renderFiles(files) {
    var tableBody = document.getElementById('filesTableBody');
    tableBody.innerHTML = '';

    if (!files.length) {
        setEmptyRow('Файлов пока нет');
        return;
    }

    files.forEach(function (item) {
        var row = document.createElement('tr');

        var nameCell = document.createElement('td');
        var name = document.createElement('div');
        name.className = 'file-name';
        name.innerText = item.filename || 'Файл';
        nameCell.appendChild(name);

        var sizeCell = document.createElement('td');
        sizeCell.className = 'text-nowrap text-muted';
        sizeCell.innerText = fileSize(item.size);

        var dateCell = document.createElement('td');
        dateCell.className = 'text-nowrap text-muted';
        dateCell.innerText = formatDate(item.created_at);

        var linkCell = document.createElement('td');
        linkCell.className = 'file-link';
        var input = document.createElement('input');
        input.className = 'form-control form-control-sm';
        input.value = item.direct;
        input.readOnly = true;
        input.addEventListener('focus', function () {
            input.select();
        });
        linkCell.appendChild(input);

        var actionCell = document.createElement('td');
        actionCell.className = 'text-end';
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-primary copy-status';
        button.innerText = 'Копировать';
        button.addEventListener('click', function () {
            copyText(item.direct, button);
        });
        actionCell.appendChild(button);

        row.appendChild(nameCell);
        row.appendChild(sizeCell);
        row.appendChild(dateCell);
        row.appendChild(linkCell);
        row.appendChild(actionCell);
        tableBody.appendChild(row);
    });
}

function paginationItem(label, page, disabled, active) {
    var item = document.createElement('li');
    item.className = 'page-item';
    if (disabled) {
        item.classList.add('disabled');
    }
    if (active) {
        item.classList.add('active');
    }

    var link = document.createElement('button');
    link.type = 'button';
    link.className = 'page-link';
    link.innerText = label;
    link.disabled = disabled;
    link.addEventListener('click', function () {
        loadFiles(page);
    });

    item.appendChild(link);
    return item;
}

function renderPagination(data) {
    var info = document.getElementById('filesPageInfo');
    var pagination = document.getElementById('filesPagination');
    pagination.innerHTML = '';

    if (!data.total) {
        info.innerText = '';
        return;
    }

    var start = (data.page - 1) * data.per_page + 1;
    var end = Math.min(data.page * data.per_page, data.total);
    info.innerText = start + '-' + end + ' из ' + data.total;

    pagination.appendChild(paginationItem('Назад', data.page - 1, !data.has_prev, false));

    var from = Math.max(1, data.page - 2);
    var to = Math.min(data.pages || 1, data.page + 2);
    for (var page = from; page <= to; page += 1) {
        pagination.appendChild(paginationItem(String(page), page, false, page === data.page));
    }

    pagination.appendChild(paginationItem('Вперед', data.page + 1, !data.has_next, false));
}

function loadFiles(page) {
    currentPage = page || currentPage;
    fetch('/api/files?page=' + currentPage + '&per_page=' + perPage)
        .then(function (response) {
            if (!response.ok) {
                throw new Error('Не удалось загрузить список файлов');
            }
            return response.json();
        })
        .then(function (data) {
            renderFiles(data.files || []);
            renderPagination(data);
        })
        .catch(function (error) {
            setEmptyRow(error.message);
        });
}

function initialize() {
    var form = document.getElementById('my-awesome-dropzone');
    if (form && !form.dropzone) {
        new Dropzone(form, Dropzone.options.myAwesomeDropzone);
    }
    loadFiles(1);
}

document.addEventListener('DOMContentLoaded', initialize);
