var json = '[{"id":50,"level":1},{"id":5,"level":0},{"id":10,"level":2}]'
var color = ["#B54434", "#E2943B", "#F7C242"]

check();

var interval;
function check() {
    var list;
    interval = setInterval(function() {
        if ((list = document.getElementById(":iu")) != null) {
            clearInterval(interval);
            list.addEventListener("DOMSubtreeModified", check, false);
            var lower = list.childNodes[0].childNodes[0].childNodes[0].innerHTML - 1;
            var upper = list.childNodes[0].childNodes[0].childNodes[2].innerHTML - 1;
            mark(lower, upper);
        }
    }, 500)
}

function mark(lower, upper) {
    var data = JSON.parse(json);
    for (var i = 0; i < data.length; i++) {
        var id = data[i]["id"];
        var level = color[data[i]["level"]];
        if (id >= lower && id <= upper) {
            document.getElementsByClassName("zA")[id - lower].style.backgroundColor=level;
        }
    }
}
