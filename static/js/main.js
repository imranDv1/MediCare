var csrftoken = $('meta[name="csrf-token"]').attr('content');
$.ajaxPrefilter(function(options, originalOptions, jqXHR) {
    if (options.type.toLowerCase() !== 'get') {
        jqXHR.setRequestHeader('X-CSRFToken', csrftoken);
    }
});

$(document).ready(function() {
    $('.sidebar-toggler, #sidebarToggler').on('click', function() {
        $('.sidebar').toggleClass('show');
        $('.sidebar').toggleClass('collapsed');
    });

    setTimeout(function() {
        $('.toast').toast('hide');
    }, 5000);

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (el) { return new bootstrap.Tooltip(el) });

    $('.btn-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
        }
    });

    $('#select-all').on('change', function() {
        $('.select-item').prop('checked', this.checked);
    });

    if ($('input[type="date"]').length) {
        $('input[type="date"]').attr('placeholder', 'dd/mm/yyyy');
    }

    $('#id_image').on('change', function(e) {
        var reader = new FileReader();
        reader.onload = function(e) {
            $('#image-preview').attr('src', e.target.result).show();
        };
        if (this.files[0]) reader.readAsDataURL(this.files[0]);
    });
});

function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    var d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}
