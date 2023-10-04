(function () {
    'use strict';

    var TableFilter = (function () {
        var Arr = Array.prototype;
        var input;

        function onInputEvent(e) {
            input = e.target;
            var table1 = document.getElementsByClassName(input.getAttribute('data-table'));
            Arr.forEach.call(table1, function (table) {
                Arr.forEach.call(table.tBodies, function (tbody) {
                    Arr.forEach.call(tbody.rows, filter);
                });
            });
        }

        function filter(row) {
            var text = row.textContent.toLowerCase();
            //console.log(text);
            var val = input.value.toLowerCase();
            //console.log(val);
            row.style.display = text.indexOf(val) === -1 ? 'none' : 'table-row';
        }

        return {
            init: function () {
                var inputs = document.getElementsByClassName('table-filter');
                Arr.forEach.call(inputs, function (input) {
                    input.oninput = onInputEvent;
                });
            }
        };

    })();

    /*console.log(document.readyState);
      document.addEventListener('readystatechange', function() {
          if (document.readyState === 'complete') {
        console.log(document.readyState);
              TableFilter.init();
          }
      }); */

    TableFilter.init();
})();
