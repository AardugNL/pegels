odoo.define('timesheet_writing.image_upload', function (require) {
'use strict';

    $(document).ready(function () {
        function readURL(input) {
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    $('#imgPreview').attr('src', e.target.result);
                }
                reader.readAsDataURL(input.files[0]);
            }
        }
        $("#inputFile").change(function () {
            readURL(this);
        });
    });
});
