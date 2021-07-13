odoo.define('bnk_recruitment_website.recruitment', (require) => {
    'use strict'
    let ApplicationForm = {
        init: function () {
            this._load_events()
        },
        _load_events: () => {
            $('#skills').select2();
            $("#dob").datepicker({changeMonth: true, changeYear: true, yearRange: "-61:+0", dateFormat: "dd/mm/yy"});
        }
    }
    $(document).ready(() => {
        ApplicationForm.init()
    })

})