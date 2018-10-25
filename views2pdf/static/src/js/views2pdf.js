odoo.define('views2pdf.views2pdf', function (require) {
        "use strict";
    var core = require('web.core');
    var Model = require('web.DataModel');
    var WebClient = require('web.WebClient');
    var session = require('web.session');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var PivotView = require('web.PivotView');
    var GraphView = require('web.GraphView');
    var CalendarView = require('web_calendar.CalendarView');
    var KanbanView = require('web_kanban.KanbanView');

    var _t = core._t;
    var QWeb = core.qweb;

    // override FormView

    FormView.include({

        render_buttons: function() {
            var result = this._super.apply(this, arguments); // Sets if (this.$buttons) {
            var self = this;
            if (this.$buttons) {
                    this.$buttons.on('click', '#create_pdf', function (e) {
                        e.preventDefault();
                        self.generate_pdf();

                    });
                    }
        },
        generate_pdf: function() {
            var form = $('.o_form_sheet'),
            cache_width = form.width(),
            a4 = [800, 841.89]; // for a4 size paper width and height
            // create canvas object
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var
                     img = canvas.toDataURL("image/png"),
                     doc = new jsPDF({
                         unit: 'px',
                         format: 'letter',
                         orientation: 'landscape'
                     });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('form.pdf');
                    form.width(cache_width);
                });
            }

            $('body').scrollTop(0);
            createPDF();

        },

    });


    // override ListView

    ListView.include({

        render_buttons: function() {
            var result = this._super.apply(this, arguments); // Sets if (this.$buttons) {
            var self = this;
            if (this.$buttons) {
                    this.$buttons.on('click', '#create_pdf', function (e) {
                        e.preventDefault();
                        self.generate_pdf();

                    });
                    }
        },
        generate_pdf: function() {
            var form = $('.o_list_view'),
            cache_width = form.width(),
            a4 = [800, 841.89]; // for a4 size paper width and height
            // create canvas object
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var
                     img = canvas.toDataURL("image/png"),
                     doc = new jsPDF({
                         unit: 'px',
                         format: 'letter',
                         orientation: 'landscape'
                     });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('list.pdf');
                    form.width(cache_width);
                });
            }

            $('body').scrollTop(0);
            createPDF();

        },

    });

    // override GraphView

    GraphView.include({

        render_buttons: function() {
            var result = this._super.apply(this, arguments); // Sets if (this.$buttons) {
            var self = this;
            if (this.$buttons) {
                    this.$buttons.on('click', '#create_pdf', function (e) {
                        e.preventDefault();
                        self.generate_pdf();

                    });
                    }
        },
        generate_pdf: function() {
            function createPDF() {
             var svg = $('.o_view_manager_content').find('svg')[0];
                        svgAsPngUri(svg, {}, function(uri) {
                            var doc = new jsPDF({
                                 unit: 'px',
                                 format: 'letter',
                                 orientation: 'landscape'
                             });
                            var title = $('ol.breadcrumb').find('li.active').html();
                            doc.setFont("helvetica");
                            doc.setFontType("bold");
                            doc.setTextColor(0,0,255);
                            doc.text(title, 20, 30);
                            doc.addImage(uri, 'PNG', 0, 60, 500,300);
                            doc.save('graph.pdf');
                    });
            }

            $('body').scrollTop(0);
            createPDF();

        },

    });

     // override KanbanView

    KanbanView.include({

        render_buttons: function() {
            var result = this._super.apply(this, arguments); // Sets if (this.$buttons) {
            var self = this;
            if (this.$buttons) {
                    this.$buttons.on('click', '#create_pdf', function (e) {
                        e.preventDefault();
                        self.generate_pdf();

                    });
                    }
        },
        generate_pdf: function() {
            var form = $('.o_view_manager_content'),
            cache_width = form.width(),
            a4 = [800, 841.89]; // for a4 size paper width and height
            // create canvas object
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var
                     img = canvas.toDataURL("image/png"),
                     doc = new jsPDF({
                         unit: 'px',
                         format: 'letter',
                         orientation: 'landscape'
                     });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('kanban.pdf');
                    form.width(cache_width);
                });
            }

            $('body').scrollTop(0);
            createPDF();

        },

    });
    // override PivotView

    PivotView.include({

        render_buttons: function() {
            var result = this._super.apply(this, arguments); // Sets if (this.$buttons) {
            var self = this;
            if (this.$buttons) {
                    this.$buttons.on('click', '#create_pdf', function (e) {
                        e.preventDefault();
                        self.generate_pdf();

                    });
                    }
        },
        generate_pdf: function() {
            var form = $('.o_view_manager_content'),
            cache_width = form.width(),
            a4 = [800, 841.89]; // for a4 size paper width and height
            // create canvas object
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var
                     img = canvas.toDataURL("image/png"),
                     doc = new jsPDF({
                         unit: 'px',
                         format: 'letter',
                         orientation: 'landscape'
                     });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('pivot.pdf');
                    form.width(cache_width);
                });
            }

            $('body').scrollTop(0);
            createPDF();

        },

    });
    // override CalendarView

    CalendarView.include({
        render_buttons: function() {
            var result = this._super.apply(this, arguments); // Sets if (this.$buttons) {
            var self = this;
            if (this.$buttons) {
                    this.$buttons.on('click', '#create_pdf', function (e) {
                        e.preventDefault();
                        self.generate_pdf();

                    });
                    }

        },
        generate_pdf: function() {
            var form = $('.o_calendar_widget'),
            cache_width = form.width(),
            a4 = [800, 841.89]; // for a4 size paper width and height
            // create canvas object
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var
                     img = canvas.toDataURL("image/png"),
                     doc = new jsPDF({
                         unit: 'px',
                         format: 'letter',
                         orientation: 'landscape'
                     });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('calendar.pdf');
                    form.width(cache_width);
                });
            }

            $('body').scrollTop(0);
            createPDF();

        },

    });
});